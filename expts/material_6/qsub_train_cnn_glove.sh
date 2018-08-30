#!/bin/sh
#$ -cwd
#$ -o /export/a08/fwang/tfmtl/expts/material_6/cnn_glove.o
#$ -e /export/a08/fwang/tfmtl/expts/material_6/cnn_glove.e
#$ -M fwang40@jhu.edu
#$ -l 'gpu=1,mem_free=30G,ram_free=30G,hostname="b1*|c*"''
#$ -pe smp 2
#$ -V
#$ -q g.q

source /home/fwang/.bashrc
source /home/fwang/gpu/bin/activate
cd /export/a08/fwang/tfmtl/expts/material_6/
CUDA_VISIBLE_DEVICES=`free-gpu` python ../scripts/discriminative_driver.py \
       --model mult \
       --mode train \
       --num_train_epochs 50 \
       --checkpoint_dir ./data/ckpt/cnn_glove/ \
       --datasets GOV LIF BUS LAW HEA MIL \
       --dataset_paths data/tf/merged/BUS_GOV_HEA_LAW_LIF_MIL/min_1_max_-1_vocab_-1_glove.6B.300d_expand/GOV data/tf/merged/BUS_GOV_HEA_LAW_LIF_MIL/min_1_max_-1_vocab_-1_glove.6B.300d_expand/LIF/ data/tf/merged/BUS_GOV_HEA_LAW_LIF_MIL/min_1_max_-1_vocab_-1_glove.6B.300d_expand/BUS/ data/tf/merged/BUS_GOV_HEA_LAW_LIF_MIL/min_1_max_-1_vocab_-1_glove.6B.300d_expand/LAW/ data/tf/merged/BUS_GOV_HEA_LAW_LIF_MIL/min_1_max_-1_vocab_-1_glove.6B.300d_expand/HEA/ data/tf/merged/BUS_GOV_HEA_LAW_LIF_MIL/min_1_max_-1_vocab_-1_glove.6B.300d_expand/MIL/ \
       --class_sizes 2 2 2 2 2 2 \
       --vocab_size_file data/tf/merged/BUS_GOV_HEA_LAW_LIF_MIL/min_1_max_-1_vocab_-1_glove.6B.300d_expand/vocab_size.txt \
       --encoder_config_file encoders.json \
       --architecture cnn_expand_glove \
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
       --log_file cnn_glove.log \
       --topic_field_name text
