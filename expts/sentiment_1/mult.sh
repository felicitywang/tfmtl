python ../scripts/discriminative_driver.py --datasets LMRD SSTb --dataset_paths data/tf/merged/LMRD_SSTb/min_50_max_-1/LMRD/ data/tf/merged/LMRD_SSTb/min_50_max_-1/SSTb/ --class_sizes 2 5 --vocab_path data/tf/merged/LMRD_SSTb/min_50_max_-1/vocab_size.txt --model mult --encoder_architecture paragram_phrase_tied_word_embeddings
