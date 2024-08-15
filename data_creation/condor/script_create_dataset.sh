#!/bin/bash

NJOBS=${2}
OUTDIR=/eos/experiment/fcc/ee/idea_tracking/
CONFIG=${1}  
SAMPLE=${3}
NEVT=100

ORIG_PARAMS=("$@")
set --
source /cvmfs/sw-nightlies.hsf.org/key4hep/setup.sh
set -- "${ORIG_PARAMS[@]}"

python submit_jobs.py --njobs $NJOBS \
                        --queue espresso \
                        --outdir $OUTDIR \
                        --configuration $CONFIG \
                        --script run_sequence_global.sh \
                        --sample $SAMPLE \
                        --numEvents $NEVT



