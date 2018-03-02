# Copyright 2018 Johns Hopkins University. All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or  implied.
# See the License for the specific language governing permissions and
# limitations under the License.
# ============================================================================

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

from six.moves import xrange
from operator import mul
from itertools import product

import tensorflow as tf

from tensorflow.contrib.training import HParams

from mtl.mlvae.vae import log_normal
from mtl.mlvae.vae import gaussian_sample
from mtl.mlvae.vae import get_tau

logging = tf.logging
kl_divergence = tf.contrib.distributions.kl_divergence


def default_hparams():
  return HParams(qy_mlp_hidden_dim=512,
                 qy_mlp_num_layer=2,
                 qz_mlp_hidden_dim=512,
                 qz_mlp_num_layer=2,
                 latent_dim=256,
                 tau0=0.5,
                 decay_tau=False,
                 alpha=0.5,
                 label_prior_type="uniform",
                 expectation="exact",
                 labels_key="label",
                 inputs_key="inputs",
                 targets_key="targets",
                 loss_reduce="even",
                 dtype='float32')


def generative_loss(nll_x, labels, qy_logits, py_logits, z, zm, zv,
                    zm_prior, zv_prior):
  nll_ys = []
  kl_ys = []
  for label_key, label_val in labels.items():
    qy_logit = qy_logits[label_key]
    py_logit = py_logits[label_key]
    if label_val is None:
      qcat = Categorical(logits=qy_logit, name='qy_cat_{}'.format(label_key))
      pcat = Categorical(logits=py_logit, name='py_cat_{}'.format(label_key))
      kl_ys += [kl_divergence(qcat, pcat)]
    else:
      nll_ys += [tf.nn.sparse_softmax_cross_entropy_with_logits(
        logits=py_logit,
        labels=label_val)]
  assert len(nll_ys) > 0
  assert len(kl_ys) > 0
  nll_y = tf.add_n(nll_ys)
  kl_y = tf.add_n(kl_ys)
  kl_z = log_normal(z, zm, zv) - log_normal(z, zm_prior, zv_prior)
  return nll_x + nll_y + kl_y + kl_z


def tile_over_batch_dim(logits, batch_size):
  assert len(logits.get_shape().as_list()) == 1
  logits = tf.expand_dims(logits, 0)  # add batch dim
  return tf.tile(logits, [batch_size, 1])


class JointMultiLabelVAE(object):
  def __init__(self,
               is_training=True,
               prior=None,
               class_sizes=None,
               encoders=None,
               decoders=None,
               hp=None):
    """
    is_training: include regularization?
    class_sizes: map from feature names to cardinality of label sets
    dataset_order: *ordered* list of features
    encoders: one per label (i.e. dataset)
    decoders: one per label (i.e. dataset)
    """

    assert class_sizes is not None
    assert encoders.keys() == decoders.keys()

    self._encoders = encoders
    self._decoders = decoders

    if hp is None:
      tf.logging.info("Using default hyper-parameters; none provided.")
      hp = default_hparams()
    self._hp = hp

    self._class_sizes = class_sizes

    # Intermediate loss values
    self._task_nll_x = dict()
    self._task_loss = dict()

    ########################### Generative Networks ###########################

    output_size = reduce(mul, class_sizes.values())
    tf.logging.info("Size of output space of joint distribution: %d",
                    output_space)

    # ln p(y_1, ..., y_K)

    def fixed_prior():
      if len(prior.shape) == 1:
        # Joint prior ln p(y_1, ..., y_K) as one vector where, for
        # two labels Y1 and Y2 with values {a, b} and {1, 2}:
        #
        #  prior[0] = ln p(Y1 = a, Y2 = 1)
        #  prior[1] = ln p(Y1 = a, Y2 = 2)
        #  prior[2] = ln p(Y1 = b, Y2 = 1)
        #  prior[4] = ln p(Y1 = b, Y2 = 2)
        #
        assert prior.shape[0] == output_size
        return tf.constant(prior)
      elif len(prior.shape) == 2:
        # Independent priors: ln p(y_1), ..., ln p(y_K)
        raise ValueError("unimplemented")
        # flat_prior = np.zeros([output_size])
        # sizes = class_sizes.values()
        # iters = [xrange(R) for R in sizes]
        # i = 0
        # for idx in product(iters):
        #   flat_prior[i] = reduce(sum,
        #                          [np.log(x) for x in prior[idx]])
        #   i += 1
      else:
        raise ValueError("bad prior")

    def uniform_prior():
      return tf.zeros([output_size])

    def learned_prior():
      return tf.get_variable('prior_weight', shape=[output_size],
                             trainable=True)

    if hp.label_prior_type == "uniform":
      prior_fn = uniform_prior
    elif hp.label_prior_type == "learned":
      prior_fn = learned_prior
    elif hp.label_prior_type == "fixed":
      if prior is None:
        raise ValueError("specified prior type but no prior given")
      prior_fn = fixed_prior
    else:
      raise ValueError("unrecognized exception")

    self._ln_py_template = tf.make_template('py', prior_fn,
                                            output_size=label_size)

    # p(z | y_1, ..., y_K)
    self._ln_pz_template = tf.make_template('pz', MLP_gaussian_posterior,
                                            hidden_dim=hp.mlp_hidden_dim,
                                            latent_dim=hp.latent_dim)

    ########################### Inference Networks ############################

    # ln q(y_1, ..., y_K | x)
    self._log_qy_template = tf.make_template('qy', MLP_unnormalized_log_categorical,
                                             output_size=output_size,
                                             hidden_dim=hp.qy_mlp_hidden_dim,
                                             num_layer=hp.qy_mlp_num_layer)

    # ln q(z | x, y_1, ..., y_K)
    self._log_qz_template = tf.make_template('qz', MLP_gaussian_posterior,
                                             hidden_dim=hp.qz_mlp_hidden_dim,
                                             num_layer=hp.qz_mlp_num_layer,
                                             latent_dim=hp.latent_dim)


    # NOTE: In general we will probably use a constant value for tau.
    self._tau = get_tau(hp, decay=hp.decay_tau)

  def py_logits(self):
    return self._py_template()

  def qy_logits(self, features):
    return self._qy_templates(features)

  def pz_mean_var(self, ys):
    return self._pz_template(ys)

  def qz_mean_var(self, features, ys):
    assert type(ys) is list
    return self._qz_template([features] + ys)

  def sample_y(self, logits, name):
    # TODO(noa): check parameter sharing between tasks
    log_qy = ExpRelaxedOneHotCategorical(self._tau,
                                         logits=logits,
                                         name='log_qy_{}'.format(name))
    y = tf.exp(log_qy.sample())
    return y

  def get_predictions(self, inputs, feature_name):
    features = self.encode(inputs, feature_name)
    logits = self.qy_logits(feature_name, features)
    probs = tf.nn.softmax(logits)
    return tf.argmax(probs, axis=1)

  def get_task_discriminative_loss(self, task, labels, features):
    nll_ys = []
    for label_key, label_val in labels.items():
      if label_val is not None:
        nll_ys += [tf.nn.sparse_softmax_cross_entropy_with_logits(
          labels=label_val,
          logits=self.qy_logits(label_key, features),
          name='d_loss_{}'.format(label_key))]
    assert len(nll_ys)
    return tf.add_n(nll_ys)

  def get_task_generative_loss(self, task, labels, features, batch):
    ys = {}
    qy_logits = {}
    py_logits = {}
    batch_size = tf.shape(features)[0]
    for label_key, label_val in labels.items():
      py_logits[label_key] = tile_over_batch_dim(self.py_logits(label_key),
                                                 batch_size)
      if label_val is None:
        qy_logits[label_key] = self.qy_logits(label_key, features)
        ys[label_key] = self.sample_y(qy_logits[label_key], label_key)
      else:
        qy_logits[label_key] = None
        ys[label_key] = tf.one_hot(label_val, self._class_sizes[label_key])
    ys_list = ys.values()
    zm, zv = self.qz_mean_var(features, ys_list)
    z = gaussian_sample(zm, zv)
    zm_prior, zv_prior = self.pz_mean_var(ys_list)
    markov_blanket = tf.concat([z], axis=1)
    self._task_nll_x[task] = nll_x = self.decode(batch, markov_blanket, task)
    return generative_loss(nll_x, labels, qy_logits, py_logits, z, zm, zv,
                           zm_prior, zv_prior)

  def get_multi_task_loss(self, task_batches):
    losses = []
    for task_name, batch in task_batches.items():
      labels = {k: None for k in task_batches.keys()}
      labels[task_name] = batch[self.hp.labels_key]
      if self.hp.loss_reduce == "even":
        with tf.name_scope(task_name):
          loss = self.get_loss(task_name, labels, batch)
          losses.append(loss)
          self._task_loss[task_name] = loss
      else:
        raise ValueError("bad loss combination type: %s" %
                         (self.hp.loss_reduce))
    return tf.add_n(losses, name='combined_mt_loss')

  def get_loss(self, task_name, labels, batch):
    # Encode the inputs using a task-specific encoder
    features = self.encode(batch, task_name)
    g_loss = self.get_task_generative_loss(task_name, labels,
                                           features, batch)
    assert len(g_loss.get_shape().as_list()) == 1
    d_loss = self.get_task_discriminative_loss(task_name, labels, features)
    assert len(d_loss.get_shape().as_list()) == 1
    a = self.hp.alpha
    assert a >= 0.0 and a <= 1.0, a
    return ((1. - a) * tf.reduce_mean(g_loss)) + (a * tf.reduce_mean(d_loss))

  def encode(self, inputs, task_name):
    return self._encoders[task_name](inputs)

  def decode(self, targets, context, task_name):
    return self._decoders[task_name](targets, context)

  def get_task_loss(self, task_name):
    return self._task_loss[task_name]

  def get_task_nll_x(self, task_name):
    return self._task_nll_x[task_name]

  @property
  def hp(self):
    return self._hp

  @property
  def tau(self):
    return self._tau
