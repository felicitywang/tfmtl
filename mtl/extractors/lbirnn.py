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

import tensorflow as tf
from six.moves import xrange


def get_multi_cell(cell_type, cell_size, num_layers):
  cells = [cell_type(cell_size) for _ in xrange(num_layers)]
  return tf.contrib.rnn.MultiRNNCell(cells)


def _lbirnn_helper(inputs,
                   lengths,
                   indices=None,
                   num_layers=2,
                   cell_type=tf.contrib.rnn.BasicLSTMCell,
                   cell_size=64,
                   initial_state_fwd=None,
                   initial_state_bwd=None):
  """Stacked linear chain bi-directional RNN

  Inputs
  _____
    inputs: batch of size [batch_size, batch_len, embed_size]
    lengths: batch of size [batch_size]
    indices: which token index in each batch example should be output
             shape: [batch_size] or [batch_size, 1]
    num_layers: number of stacked layers in the bi-RNN
    cell_type: type of RNN cell to use (e.g., LSTM, GRU)
    cell_size: cell's output size
    initial_state_fwd: initial state for forward direction
    initial_state_bwd: initial state for backward direction

  Outputs
  _______
    If the input word vectors have dimension D and indices is None,
    the output is a Tensor of size
      [batch_size, batch_len, cell_size_fwd + cell_size_bwd]
        = [batch_size, batch_len, 2*cell_size].

    If indices is not None, the output is a Tensor of size
      [batch_size, cell_size_fwd + cell_size_bwd]
        = [batch_size, 2*cell_size]
  """

  # reverse each batch example up through its length, maintaining right-padding
  inputs_rev = tf.reverse_sequence(inputs, lengths, batch_axis=0, seq_axis=1)

  cells_fwd = get_multi_cell(cell_type, cell_size, num_layers)
  cells_bwd = get_multi_cell(cell_type, cell_size, num_layers)

  batch_size = tf.shape(inputs)[0]
  if initial_state_fwd is None:
    initial_state_fwd = cells_fwd.zero_state(batch_size,
                                             tf.float32)
  else:
    # replace None values with zero states
    initial_state_fwd = list(initial_state_fwd)
    for i, c in enumerate(initial_state_fwd):
      if c is None:
        initial_state_fwd[i] = cell_type(cell_size).zero_state(batch_size,
                                                               tf.float32)
    initial_state_fwd = tuple(initial_state_fwd)

  if initial_state_bwd is None:
    initial_state_bwd = cells_bwd.zero_state(batch_size,
                                             tf.float32)
  else:
    # replace None values with zero states
    initial_state_bwd = list(initial_state_bwd)
    for i, c in enumerate(initial_state_bwd):
      if c is None:
        initial_state_bwd[i] = cell_type(cell_size).zero_state(batch_size,
                                                               tf.float32)
    initial_state_bwd = tuple(initial_state_bwd)

  assert len(initial_state_fwd) == num_layers, "length of initial_state_fwd " \
                                               "must equal num_layers: " \
                                               "got {}, num_layers={}".format(
                                               len(initial_state_fwd),
                                               num_layers)
  assert len(initial_state_bwd) == num_layers, "length of initial_state_bwd " \
                                               "must equal num_layers: " \
                                               "got {}, num_layers={}".format(
                                               len(initial_state_bwd),
                                               num_layers)

  outputs_fwd, states_fwd = tf.nn.dynamic_rnn(cells_fwd,
                                              inputs,
                                              sequence_length=lengths,
                                              initial_state=initial_state_fwd,
                                              time_major=False,
                                              scope="rnn_fwd")

  tmp, states_bwd = tf.nn.dynamic_rnn(cells_bwd,
                                      inputs_rev,
                                      sequence_length=lengths,
                                      initial_state=initial_state_bwd,
                                      time_major=False,
                                      scope="rnn_bwd")
  # reverse backward-pass outputs so they align with the forward-pass outputs
  outputs_bwd = tf.reverse_sequence(tmp, lengths, batch_axis=0, seq_axis=1)

  if indices is not None:
    # row index [[0], [1], ..., [N]]
    r = tf.range(batch_size)
    r = tf.expand_dims(r, 1)

    # make sure indices are able to be concatenated with range
    # i.e., of the form [[idx_0], [idx_1], ..., [idx_N]]
    rank = len(indices.get_shape().as_list())
    if rank == 1:
      indices = tf.expand_dims(indices, 1)
    elif rank == 2:
      pass
    else:
      raise ValueError("indices doesn't have rank 1 or 2: rank=%d" % (rank))

    idx = tf.concat([r, indices], axis=1)

    # get the (indices[i])-th token's output from row i
    outputs_fwd = tf.gather_nd(outputs_fwd, idx)
    outputs_bwd = tf.gather_nd(outputs_bwd, idx)

  return (outputs_fwd, outputs_bwd), (states_fwd, states_bwd)


def lbirnn(inputs,
           lengths,
           indices=None,
           num_layers=2,
           cell_type=tf.contrib.rnn.BasicLSTMCell,
           cell_size=64,
           initial_state_fwd=None,
           initial_state_bwd=None):
  o, _ = _lbirnn_helper(inputs,
                        lengths,
                        indices=indices,
                        num_layers=num_layers,
                        cell_type=cell_type,
                        cell_size=cell_size,
                        initial_state_fwd=initial_state_fwd,
                        initial_state_bwd=initial_state_bwd)
  (outputs_fwd, outputs_bwd) = o
  outputs = tf.concat([outputs_fwd, outputs_bwd], axis=-1)
  return outputs


def serial_lbirnn(inputs,
                  lengths,
                  indices,
                  num_layers,
                  cell_type,
                  cell_size,
                  initial_state_fwd,
                  initial_state_bwd):
  """Serial stacked linear chain bi-directional RNN

  If `indices` is specified for the last stage, the outputs of the tokens
  in the last stage as specified by `indices` will be returned.
  If `indices` is None for the last stage, the encodings for all tokens
  in the sequence are returned.

  Inputs
  _____
    All arguments denoted with (*) should be given as lists,
    one element per stage in the series. The specifications given
    below are for a single stage.

    inputs (*): Tensor of size [batch_size, batch_len, embed_size]
    lengths (*): Tensor of size [batch_size]
    indices: Tensor of which token index in each batch item should be output;
             shape: [batch_size] or [batch_size, 1]
    num_layers: number of stacked layers in the bi-RNN
    cell_type: type of RNN cell to use (e.g., LSTM, GRU)
    cell_size: cell's output size
    initial_state_fwd: initial state for forward direction, may be None
    initial_state_bwd: initial state for backward direction, may be None

  Outputs
  _______
  If the input word vectors have dimension D and the series has N stages:
  if `indices` is not None:
    the output is a Tensor of size [batch_size, cell_size]
  if `indices` is None:
    the output is a Tensor of size [batch_size, batch_len, cell_size]
  """

  lists = [inputs, lengths]
  it = iter(lists)
  num_stages = len(next(it))
  if not all(len(l) == num_stages for l in it):
    raise ValueError("all list arguments must have the same length")

  assert num_stages > 0, "must specify arguments for " \
                         "at least one stage of serial bi-RNN"

  fwd_ = initial_state_fwd
  bwd_ = initial_state_bwd
  for i in xrange(num_stages):
    with tf.variable_scope("serial_lbirnn_{}".format(i)):
      inputs_ = inputs[i]
      lengths_ = lengths[i]
      if i == num_stages - 1:
        # Use the user-specified indices on the last stage
        indices_ = indices
      else:
        indices_ = None

      if fwd_ is not None:
        assert len(fwd_) == num_layers, "must specify initial state " \
                                        "for forward pass for all layers " \
                                        "of serial bi-RNN"
      if bwd_ is not None:
        assert len(bwd_) == num_layers, "must specify initial state " \
                                        "for forward pass for all layers " \
                                        "of serial bi-RNN"

      o, s = _lbirnn_helper(inputs_,
                            lengths_,
                            indices=indices_,
                            num_layers=num_layers,
                            cell_type=cell_type,
                            cell_size=cell_size,
                            initial_state_fwd=fwd_,
                            initial_state_bwd=bwd_)
      (outputs_fwd, outputs_bwd), (states_fwd, states_bwd) = o, s
      # Update arguments for next stage
      fwd_ = states_fwd
      bwd_ = states_bwd

  outputs = tf.concat([outputs_fwd, outputs_bwd], axis=-1)

  return outputs