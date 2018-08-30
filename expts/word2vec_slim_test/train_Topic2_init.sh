python ../scripts/discriminative_driver.py \
       --model mult \
       --mode train \
       --num_train_epochs 50 \
       --checkpoint_dir ./data/ckpt/Topic2_pretrained_init/ \
       --experiment_name RUDER_NAACL_18 \
       --datasets Topic2 \
       --dataset_paths data/tf/single/Topic2/min_1_max_-1_vocab_-1_GoogleNews-vectors-negative300-SLIM_init \
       --class_sizes 2 \
       --vocab_size_file data/tf/single/Topic2/min_1_max_-1_vocab_-1_GoogleNews-vectors-negative300-SLIM_init/vocab_size.txt \
       --encoder_config_file encoders.json \
       --architecture serial-birnn-init-pretrained \
       --shared_mlp_layers 0 \
       --shared_hidden_dims 0 \
       --private_mlp_layers 1 \
       --private_hidden_dims 64 \
       --alphas 1 \
       --optimizer rmsprop \
       --lr0 0.001 \
       --tuning_metric Acc \
       --topics_path data/json/Topic2/data.json.gz \
       --seed 42 \
       --log_file Topic2_init.log
