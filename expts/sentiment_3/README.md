## datasets

type|name|#items|#labels|unit|summary|split|unlabeled
---|---|---|---|---|---|---|---
sentiment|IMDb|600,000|2|paragraph|IMDb movie reviews|train:test=300,000:300,000|none
sentiment|RTU|739,903|2|paragraph|Rotten Tomatoes user movie reviews|train:test=737,903:2000|none

## requirements

See `../../requirement.txt`

## file structure
- `setup.sh`: shell(bash) script to download original data files, convert them to json format, generate their shared vocabulary, and generate TFRecord files according to that vocabulary
- `write_tfrecord_merged.py`: python script to generate merged vocabulary and write TFRecord data files
- `args_merged`: arguments for the datasets that use the shared vocabulary
- `write_tfrecord_single.py`: python script to generate TFRecord files for the single dataset(without share vocabulary)
- `args_IMDb`: arguments for the dataset IMDb
- `args_RTU`: arguments for the dataset RTU
- `data/raw/`: downloaded/unzipped original data files
- `data/json/`: converted json data and basic vocabulary of the dataset
- `data/tf/merged/IMDb_RTU/min_(min_freq)_max_(max_freq)`: generated data for the given min/max vocab frequency
    - `vocab_freq.json`: frequency of all the words that appeared in the training data(merged vocabulary)
    - `vocab_v2i.json`: mapping from word to id of the used vocabulary(only words appeared > min_frequency and < max_frequency)
    - `vocab_i2v.json`: mapping from id to word(sorted by frequency) of the used vocabulary
    - `dataset_name`
        - `train.tf`, `valid.tf`, `test.tf`: train/valid/test TFRecord files
        - `unlabeled.tf`: unlabeled TFRecord files(if there is unlabeled data)
        - `args.json`: arguments of the dataset
- `data/tf/single/dataset_name/min_(min_freq)_max_(max_freq)`: generated data for the given min/max vocab frequency for the single dataset
    - `train.tf`, `valid.tf`, `test.tf`: train/valid/test TFRecord files
    - `unlabeled.tf`: unlabeled TFRecord files(if there is unlabeled data)
    - `args.json`: arguments of the dataset
    - `vocab_freq.json`: frequency of all the words that appeared in the training data
    - `vocab_v2i.json`: mapping from word to id of the used vocabulary(only words appeared > min_frequency and < max_frequency)
    - `vocab_i2v.json`: mapping from id to word(sorted by frequency) of the used vocabulary


## steps

1. modify arguments in `args_merged.json`
2. run `setup.sh` to generate TFRecord files with merged vocabulary
3. (optional)
    - modify arguments in `args_IMDb.json` or `args_RTU.json`
    - generate TFRecord files for the single datasetrun by
        - `python ../scripts/write_tfrecords_single.py IMDb`
        - `python ../scripts/write_tfrecords_single.py RTU`

### arguments for datasets
- `max_document_length`: maximum document length for the word id(-1 if not given, only useful when padding is true)
- `min_frequency`: minimum frequency to keep when generating the vocabulary
- `max_frequency`: maximum frequency to keep when generating the vocabulary
- `label_field_name`: name of the label column in the json data file
- `text_field_names`: (list)names of the text columns in the json data file
- `train_ratio`: how much data to use as training data if no splits given
- `valid_ratio`: how much data out of all the data to use as validation data if no splits are given, or how much data out of training data to use as validation data if only train/test splits are given
- `random_seed`: seed used in random spliting indices
- `subsample_ratio`: how much data to use out of all the data
- `padding`: whether to pad the word ids
- `write_bow`: whether to write bag of words in the TFRecord file


## MLP baseline
type|dataset|accuracy|min_freq
---|---|---|---
sentiment|IMDb|40.7240%|1
sentiment|RTU|?|100

### hyperparameters:
- learning rate: 0.0001
- dropout rate:0.5
- batch size: 32
- seed: 42
- max_num_epoch: 20(with early stopping)
- layers: [100, 100]
- encoding: bag of words
- train:valid = 9:1 if no valid split given

### state-of-the-art results

- IMDb:
?

- RTU:
?