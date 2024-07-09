#!/bin/bash

source /cvmfs/sw-nightlies.hsf.org/key4hep/setup.sh

OUTDIR=/afs/cern.ch/user/a/adevita/public/workDir/dataset/
CONFIG=muons_eta0017_mom50


mkdir -p "${OUTDIR}${CONFIG}/"

python submit_jobs.py  --njobs 30 \
                             --queue espresso \
                             --outdir $OUTDIR \
                             --configuration $CONFIG \
                             --script run_sequence_global.sh \
                             --sample gun \
                             --numEvents 5



