"""Create json data"""
import gzip
import json
import os

import numpy as np

from mtl.util.util import make_dir


def parse_args():
    import argparse
    p = argparse.ArgumentParser()
    p.add_argument('--seed', type=int, default=42,
                   help='random seed')
    return p.parse_args()


def main():
    global seed
    args = parse_args()
    seed = args.seed

    DOMAIN_6 = ['GOV', 'LIF', 'HEA', 'LAW', 'MIL', 'BUS']

    GOLD_PATH_SUFFIXES = ['_1000']
    SYN_PATH_SUFFIXES = ['s']

    for domain in DOMAIN_6:
        make_dir(os.path.join('data/json/', domain + '_1000'))

    for domain in DOMAIN_6:

        # TODO 1best and bag json data
        gold_path = os.path.join('data/json/', domain + 'g', 'data.json.gz')

        # TODO turk ?
        syn_path = os.path.join('data/json/', domain + 's', 'data.json.gz')

        with gzip.open(gold_path, 'rt') as gold_file:
            gold_data = json.load(gold_file)
        with gzip.open(syn_path, 'rt') as syn_file:
            syn_data = json.load(syn_file)
        print(domain, len(gold_data), len(syn_data))
        # print(set([i['label'] for i in syn_data[:1000]]))
        # print(set([i['label'] for i in syn_data[1000:]]))
        # for synthetic data assert first half pos and second neg
        assert len(syn_data) == 2000, len(syn_data)
        for i in range(1000):
            assert int(syn_data[i]['label']) == 1, str(i) + ' ' + str(
                syn_data[i]['label'])
        for i in range(1000, 2000):
            assert int(syn_data[i]['label']) == 0, str(i) + ' ' + str(
                syn_data[i]['label'])

        for pos_num in [1000]:
            data, index_dict = combine_data(gold_data, syn_data, pos_num, half)
            dir = os.path.join('data/json/', domain + '_' + str(pos_num))
            with gzip.open(os.path.join(dir, 'data.json.gz'), mode='wt') as file:
                json.dump(data, file, ensure_ascii=False)
            with gzip.open(os.path.join(dir, 'index.json.gz'), mode='wt') as file:
                json.dump(index_dict, file, ensure_ascii=False)

    # open test
    for domain in DOMAIN_6:
        for pos_num in [100, 1000]:
            dir = os.path.join('data/json/', domain + '_' + str(pos_num))
            with gzip.open(os.path.join(dir, 'data.json.gz'), mode='rt') as file:
                data = json.load(file, encoding='utf-8')
            with gzip.open(os.path.join(dir, 'index.json.gz'), mode='rt') as file:
                index_dict = json.load(file, encoding='utf-8')
            print(domain,
                  len(data),
                  len(index_dict['train']),
                  len(index_dict['valid']),
                  len(index_dict['test']))


def get_gold_data(data, half=True):
    """Take half pos and half neg as dev/test, return index list"""
    global seed
    np.random.seed(seed)

    if half:

        pos_list = []
        neg_list = []
        for i, d in enumerate(data):
            if int(d['label']) == 0:
                neg_list.append(i)
            else:
                pos_list.append(i)

        pos = np.random.permutation(np.array(pos_list))
        dev_pos, test_pos = map(list, np.split(pos, [int(len(pos_list) / 2)]))

        neg = np.random.permutation(np.array(neg_list))
        dev_neg, test_neg = map(list, np.split(neg, [int(len(neg_list) / 2)]))

        dev_pos.extend(dev_neg)
        test_pos.extend(test_neg)

        return dev_pos, test_pos

    else:
        dev = np.random.permutation(np.array(list(range(len(data)))))
        test = np.array([])


def get_syn_data(pos_num):
    """downsample positive examples to pos_num, return index list"""
    pos_list = list(range(1000))
    pos = np.random.permutation(np.array(pos_list))
    pos_list = list(np.split(pos, [pos_num])[0])
    neg_list = list(range(1000, 2000))
    pos_list.extend(neg_list)
    return pos_list


def combine_data(gold_data, syn_data, syn_pos_num, half=True):
    """Combine synthetic data and gold data, get new index_dict"""
    train_index = get_syn_data(syn_pos_num)
    dev_index, test_index = get_gold_data(gold_data, half)

    data = []
    data.extend([syn_data[i] for i in train_index])
    data.extend([gold_data[i] for i in dev_index])
    data.extend([gold_data[i] for i in test_index])
    for index, item in enumerate(data):
        item['index'] = index
    index_dict = {
        'train': list(range(len(train_index))),
        'valid': list(range(len(train_index), len(train_index) + len(dev_index))),
        'test': list(range(len(train_index) + len(dev_index),
                           len(train_index) + len(dev_index) + len(test_index)))
    }

    return data, index_dict


if __name__ == '__main__':
    main()