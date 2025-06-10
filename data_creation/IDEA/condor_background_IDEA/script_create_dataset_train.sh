#!/bin/bash

# python submit_jobs_train.py --config config_tracking.gun --outdir  /eos/experiment/fcc/ee/datasets/DC_tracking/Pythia/Zcard_CLD_background_v1/ --njobs 500 --nev 1 --queue workday

# python submit_jobs_train.py --config config_tracking.gun --outdir  /eos/experiment/fcc/ee/datasets/CLD_tracking/Pythia/Zcard_CLD_v5_v1/ --njobs 9000 --nev 1000 --queue workday


# create IDEA v03 background files:
python submit_jobs_train.py --config config_tracking.gun --outdir  /eos/experiment/fcc/ee/datasets/DC_tracking/Pythia/Zcard_CLD_background_IDEA_o1_v03 --njobs 1000 --nev 1 --queue workday


