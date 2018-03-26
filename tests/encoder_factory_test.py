#! /usr/bin/env python
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

import argparse
import tensorflow as tf

from mtl.util.encoder_factory import build_encoders


class EncoderTests(tf.test.TestCase):
  def test_template(self):
    """Manually check that the variables created for various combinations
of tied/untied embedders and extractors are correct."""

    parser = argparse.ArgumentParser()
    parser.add_argument('--architecture', default='paragram')
    parser.add_argument('--datasets', default=['SSTb', 'LMRD'])
    parser.add_argument('--encoder_config_file', default='tests/encoders.json')
    args = parser.parse_args()

    vocab_size = 1000

    with self.test_session() as sess:
      encoders = build_encoders(vocab_size, args)

      inputs1 = tf.constant([[1, 2, 3], [4, 5, 6], [7, 8, 9], [10, 11, 12]])
      lengths1 = tf.constant([3, 3, 3, 3])
      output_SSTb_1 = encoders['SSTb'](inputs=inputs1, lengths=lengths1)
      output_LMRD_1 = encoders['LMRD'](inputs=inputs1, lengths=lengths1)

      inputs2 = tf.constant([[1, 1, 1], [2, 2, 0]])
      lengths2 = tf.constant([3, 2])
      output_SSTb_2 = encoders['SSTb'](inputs=inputs2, lengths=lengths2)
      output_LMRD_2 = encoders['LMRD'](inputs=inputs2, lengths=lengths2)

      all_variables = tf.global_variables()
      trainable_variables = tf.trainable_variables()

      init_ops = [tf.global_variables_initializer(),
                  tf.local_variables_initializer()]
      sess.run(init_ops)

      all_var, train_var, s1, l1, s2, l2 = sess.run([all_variables,
                                                     trainable_variables,
                                                     output_SSTb_1,
                                                     output_LMRD_1,
                                                     output_SSTb_2,
                                                     output_LMRD_2])

      print('Encoders: {}'.format(encoders))

      print('All variables created...')
      for var in all_variables:
        print(var)

      print('Trainable variables created...')
      for var in trainable_variables:
        print(var)


if __name__ == '__main__':
    tf.test.main()