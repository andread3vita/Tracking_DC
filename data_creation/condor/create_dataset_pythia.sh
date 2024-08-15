#!/bin/bash


directory="../Pythia_generation/configurations"
NFILE=${1}

CURRPATH=$(pwd)
ORIG_PARAMS=("$@")
set --
source /cvmfs/sw-nightlies.hsf.org/key4hep/setup.sh
set -- "${ORIG_PARAMS[@]}"

WORKDIR=/afs/cern.ch/user/a/adevita/public/workDir/temp/
OUTDIR=/eos/experiment/fcc/ee/idea_tracking/
PFDIR=/afs/cern.ch/user/a/adevita/public/workDir/Tracking_DC/data_creation/

file_array=()
for file in "$directory"/*; do
    if [ -f "$file" ]; then
        filename=$(basename "$file")
        filename_no_ext="${filename%.*}"
        file_array+=("$filename_no_ext")
    fi
done

mkdir -p $WORKDIR
cd $WORKDIR

for CONFIG in "${file_array[@]}"; do

    FULLOUTDIR="${OUTDIR}/${CONFIG}/"
    mkdir -p "${FULLOUTDIR}out_sim_edm4hep/"
    mkdir -p "${FULLOUTDIR}eval/"
    mkdir -p "${FULLOUTDIR}eff/"

    cd $CURRPATH
    ./script_create_dataset.sh "${CONFIG}" $NFILE "Zcard"

    sleep 5

done

