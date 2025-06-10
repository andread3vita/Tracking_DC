#!/bin/bash

TYPE=${1}       # type: Pythia or Gun
CONFIG=${2}     # config file
VERSION=${3}    # IDEA version (2 or 3)
OPTION=${4}    # IDEA option
NFILE=${5}      # number of files

CURRPATH=$(pwd)
ORIG_PARAMS=("$@")
set --
source /cvmfs/sw-nightlies.hsf.org/key4hep/setup.sh -r 2025-05-15
set -- "${ORIG_PARAMS[@]}"

outdir=""
if [[ $VERSION -eq 1 ]]; then
    outdir="/eos/experiment/fcc/users/a/adevita/idea_v1_o2_dataset"
fi
if [[ $VERSION -eq 2 ]]; then
    outdir="/eos/experiment/fcc/users/a/adevita/idea_v2_o1_dataset/"
fi
if [[ $VERSION -eq 3 ]]; then
    outdir="/eos/experiment/fcc/users/a/adevita/idea_v3_o1_dataset"
fi


python src/submit_jobs_train.py  --queue testmatch --outdir $outdir --njobs $NFILE --type $TYPE --config $CONFIG --detectorVersion $VERSION --detectorOption $OPTION

