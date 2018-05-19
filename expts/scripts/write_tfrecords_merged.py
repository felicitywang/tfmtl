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
# =============================================================================

import json
import os
import sys

from mtl.util.dataset import merge_dict_write_tfrecord, \
  merge_pretrain_write_tfrecord
from mtl.util.util import make_dir


def main(argv):
  if argv[-1].endswith('.json'):
    args_name = argv[-1]
    argv = argv[:-1]
  else:
    args_name = 'args_merged.json'

  with open(args_name, 'rt') as file:
    args_merged = json.load(file)

  tfrecord_dir = "data/tf/merged/"
  datasets = sorted(argv[1:])
  for dataset in datasets[:-1]:
    tfrecord_dir += dataset + "_"
  tfrecord_dir += datasets[-1] + '/'

  json_dirs = [os.path.join('data/json/', dataset) for dataset in datasets]

  preproc = True
  if 'preproc' in args_merged:
    preproc = args_merged['preproc']

  vocab_all = False
  if 'vocab_all' in args_merged:
    vocab_all = args_merged['vocab_all']

  tfrecord_dir_name = "min_" + str(
    args_merged['min_frequency']) + "_max_" + str(
    args_merged['max_frequency']) + "_vocab_" + str(
    args_merged['max_vocab_size'])

  if 'pretrained_file' not in args_merged or not args_merged[
    'pretrained_file']:
    tfrecord_dir = os.path.join(tfrecord_dir, tfrecord_dir_name)
    tfrecord_dirs = [os.path.join(tfrecord_dir, dataset) for dataset in
                     datasets]
    assert [os.path.basename(tf_dir) for tf_dir in tfrecord_dirs] == [
      os.path.basename(json_dir) for json_dir in json_dirs]
    for i in tfrecord_dirs:
      make_dir(i)
    merge_dict_write_tfrecord(json_dirs=json_dirs,
                              tfrecord_dirs=tfrecord_dirs,
                              merged_dir=tfrecord_dir,
                              max_document_length=args_merged[
                                'max_document_length'],
                              max_vocab_size=args_merged['max_vocab_size'],
                              min_frequency=args_merged['min_frequency'],
                              max_frequency=args_merged['max_frequency'],
                              text_field_names=args_merged['text_field_names'],
                              label_field_name=args_merged['label_field_name'],
                              train_ratio=args_merged['train_ratio'],
                              valid_ratio=args_merged['valid_ratio'],
                              tokenizer_=args_merged['tokenizer'],
                              subsample_ratio=args_merged['subsample_ratio'],
                              padding=args_merged['padding'],
                              write_bow=args_merged['write_bow'],
                              write_tfidf=args_merged['write_tfidf'],
                              preproc=preproc,
                              vocab_all=vocab_all)
  else:
    vocab_path = args_merged['pretrained_file']
    vocab_dir = os.path.dirname(vocab_path)
    vocab_name = os.path.basename(vocab_path)
    expand_vocab = False
    if 'expand_vocab' in args_merged:
      expand_vocab = args_merged['expand_vocab']

    if expand_vocab:
      tfrecord_dir = os.path.join(
        tfrecord_dir,
        tfrecord_dir_name + '_' +
        vocab_name[:vocab_name.find('.txt')] + '_expand')
    else:
      tfrecord_dir = os.path.join(
        tfrecord_dir,
        tfrecord_dir_name + '_' +
        vocab_name[:vocab_name.find('.txt')] + '_init')

    tfrecord_dirs = [os.path.join(tfrecord_dir, dataset) for dataset in
                     datasets]
    for i in tfrecord_dirs:
      make_dir(i)
    assert [os.path.basename(tf_dir) for tf_dir in tfrecord_dirs] == [
      os.path.basename(json_dir) for json_dir in json_dirs]

    merge_pretrain_write_tfrecord(json_dirs=json_dirs,
                                  tfrecord_dirs=tfrecord_dirs,
                                  merged_dir=tfrecord_dir,
                                  vocab_dir=vocab_dir,
                                  vocab_name=vocab_name,
                                  text_field_names=args_merged[
                                    'text_field_names'],
                                  label_field_name=args_merged[
                                    'label_field_name'],
                                  max_document_length=args_merged[
                                    'max_document_length'],
                                  max_vocab_size=args_merged['max_vocab_size'],
                                  min_frequency=args_merged['min_frequency'],
                                  max_frequency=args_merged['max_frequency'],
                                  train_ratio=args_merged['train_ratio'],
                                  valid_ratio=args_merged['valid_ratio'],
                                  subsample_ratio=args_merged[
                                    'subsample_ratio'],
                                  padding=args_merged['padding'],
                                  write_bow=args_merged['write_bow'],
                                  write_tfidf=args_merged['write_tfidf'],
                                  tokenizer_=args_merged['tokenizer'],
                                  expand_vocab=expand_vocab,
                                  preproc=preproc,
                                  vocab_all=vocab_all)

  return tfrecord_dir


if __name__ == '__main__':
  main(sys.argv)
