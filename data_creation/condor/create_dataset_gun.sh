#!/bin/bash


directory="../gun/configurations"
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

echo "Building gun"
mkdir -p $WORKDIR
cd $WORKDIR

cp -r $PFDIR/gun/gun_random_angle.cpp .
cp -r $PFDIR/gun/CMakeLists.txt .
cp -r $PFDIR/gun/gun.cpp .

mkdir -p build install
cd build
cmake .. -DCMAKE_INSTALL_PREFIX=../install
make install -j 8

for CONFIG in "${file_array[@]}"; do

    FULLOUTDIR="${OUTDIR}/${CONFIG}/"
    mkdir -p "${FULLOUTDIR}out_gun/"
    mkdir -p "${FULLOUTDIR}out_sim_edm4hep/"
    mkdir -p "${FULLOUTDIR}eval/"
    mkdir -p "${FULLOUTDIR}eff/"

    cd $CURRPATH
    ./script_create_dataset.sh "${CONFIG}" $NFILE "gun"

    sleep 5

done

