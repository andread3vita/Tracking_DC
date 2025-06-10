#!/bin/bash

HOMEDIR=${1}
GUNCARD=${2}
NEV=${3}
SEED=${4}
OUTPUTDIR=${5}

DIR="/eos/experiment/fcc/ee/datasets/CLD_tracking/condor/Pythia/CLD_background_only/"
mkdir ${DIR}
mkdir ${DIR}${SEED}
cd ${DIR}${SEED}

SAMPLE="Zcard_tau_CLD"


cp /eos/experiment/fcc/users/b/brfranco/background_files/guineaPig_andrea_June2024_v23_vtx000/data${SEED}/pairs.pairs . 
cp -r /afs/cern.ch/work/m/mgarciam/private/CLD_Config_versions/CLDConfig_230924_background/CLDConfig/* .

cp /afs/cern.ch/work/m/mgarciam/private/Tracking_wcoc/data_creation/condor_background_CLD/runOverlayTiming.py .




wrapperfunction() {
     source /cvmfs/sw-nightlies.hsf.org/key4hep/setup.sh  
}
wrapperfunction



ddsim --compactFile $K4GEO/FCCee/CLD/compact/CLD_o2_v06/CLD_o2_v06.xml --outputFile out_sim_edm4hep_background_${SEED}.root \
 --steeringFile cld_steer.py --inputFiles pairs.pairs --numberOfEvents ${NEV} --random.seed ${SEED}

 
cp out_sim_edm4hep_background_${SEED}.root $OUTPUTDIR/