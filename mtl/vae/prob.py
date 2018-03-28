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
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
# ============================================================================

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

from six.moves import xrange
from itertools import product
from collections import OrderedDict
import tensorflow as tf


def entropy(logits):
  assert len(logits.get_shape()) == 2
  p = tf.nn.softmax(logits, axis=1)
  lp = tf.log(p)
  return -tf.reduce_sum(p * lp, axis=1)


def enum_events(class_sizes, cond_vals=None):
  assert type(class_sizes) is OrderedDict
  lists = []
  batch_cond = True
  first_cond_val = None
  if cond_vals is not None:
    vs = cond_vals.values()
    assert len(vs) > 0
    v0 = next(iter(vs))
    if type(v0) is int:
      batch_cond = False
    else:
      first_cond_val = v0

  for k, v in class_sizes.items():
    if cond_vals is not None and k in cond_vals:
      cond_val = cond_vals[k]
      lists.append([cond_val])
    else:
      lists.append(list(xrange(v)))

  events = [list(e) for e in list(product(*lists))]

  if cond_vals is not None and batch_cond is True:
    assert first_cond_val is not None
    for i in xrange(len(events)):  # each event is a tuple (val0, val1, ...)
      for j in xrange(len(events[i])):
        if type(events[i][j]) is int:
          y = events[i][j]
          events[i][j] = tf.ones_like(first_cond_val) * y

  return events


def normalize_logits(logits, dims=None):
  assert len(logits.get_shape()) == 2
  logits -= tf.reduce_logsumexp(logits, axis=1, keepdims=True)
  if dims is None:
    return logits
  else:
    batch_size = tf.shape(logits)[0]
    return tf.reshape(logits, [batch_size] + dims)


def marginal_log_prob(normalized_logits, target_index):
  ndims = len(normalized_logits.get_shape())
  reduce_axis = list(xrange(ndims))
  del reduce_axis[target_index+1]
  del reduce_axis[0]
  return tf.reduce_logsumexp(normalized_logits, reduce_axis)


def conditional_log_prob(normalized_logits, target_index, cond_index):
  assert target_index != cond_index
  ndims = len(normalized_logits.get_shape())
  ln_p_cond = marginal_log_prob(normalized_logits, cond_index)

  if ndims > 3:
    reduce_axis = list(xrange(ndims))
    reduce_axis.remove(target_index + 1)
    reduce_axis.remove(cond_index + 1)
    reduce_axis.remove(0)
    marginal_ln_joint = tf.reduce_logsumexp(normalized_logits,
                                            axis=reduce_axis,
                                            keepdims=False)
  else:
    marginal_ln_joint = normalized_logits

  if cond_index > target_index:
    marginal_ln_joint = tf.transpose(marginal_ln_joint,
                                     perm=[0, 2, 1])

  ln_p_cond = tf.expand_dims(ln_p_cond, axis=-1)
  final_dim = tf.shape(marginal_ln_joint)[-1]
  ln_p_cond = tf.tile(ln_p_cond, [1, 1, final_dim])
  return marginal_ln_joint - ln_p_cond
