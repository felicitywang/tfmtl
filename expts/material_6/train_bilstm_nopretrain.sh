python ../scripts/discriminative_driver.py \
       --model mult \
       --mode train \
       --num_train_epochs 50 \
       --checkpoint_dir ./data/ckpt/bilstm_nopretrain/ \
       --datasets GOV LIF BUS LAW HEA MIL \
       --dataset_paths data/tf/merged/BUS_GOV_HEA_LAW_LIF_MIL/min_1_max_-1_vocab_-1/GOV/ data/tf/merged/BUS_GOV_HEA_LAW_LIF_MIL/min_1_max_-1_vocab_-1/LIF/ data/tf/merged/BUS_GOV_HEA_LAW_LIF_MIL/min_1_max_-1_vocab_-1/BUS/ data/tf/merged/BUS_GOV_HEA_LAW_LIF_MIL/min_1_max_-1_vocab_-1/LAW/ data/tf/merged/BUS_GOV_HEA_LAW_LIF_MIL/min_1_max_-1_vocab_-1/HEA/ data/tf/merged/BUS_GOV_HEA_LAW_LIF_MIL/min_1_max_-1_vocab_-1/MIL/ \
       --class_sizes 2 2 2 2 2 2 \
       --vocab_size_file data/tf/merged/BUS_GOV_HEA_LAW_LIF_MIL/min_1_max_-1_vocab_-1/vocab_size.txt \
       --encoder_config_file encoders.json \
       --architecture bilstm_nopretrain \
       --shared_mlp_layers 1 \
       --shared_hidden_dims 128 \
       --private_mlp_layers 1 \
       --private_hidden_dims 128 \
       --alphas 0.16666667 0.16666667 0.16666667 0.16666667 0.16666667 0.16666667 \
       --optimizer rmsprop \
       --lr0 0.0005 \
       --tuning_metric Acc \
       --topics_path data/json/GOV/data.json.gz data/json/LIF/data.json.gz data/json/BUS/data.json.gz data/json/LAW/data.json.gz data/json/HEA/data.json.gz data/json/MIL/data.json.gz \
       --seed 42 \
       --log_file bilstm_nopretrain.log \
       --topic_field_name text
