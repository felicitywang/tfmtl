python ../scripts/discriminative_driver.py --datasets LMRD SWts --dataset_paths data/tf/merged/LMRD_SWts/min_0_max_-1_vocab_10000/LMRD/ data/tf/merged/LMRD_SWts/min_0_max_-1_vocab_10000/SWts/ --class_sizes 2 2 --vocab_size_file data/tf/merged/LMRD_SWts/min_0_max_-1_vocab_10000/vocab_size.txt --encoder_config_file encoders.json --model mult --input_key tokens --architecture paragram --alphas 0.5 0.5 --mode test --checkpoint_dir ./data/ckpt/mult/LMRD_SWts/
