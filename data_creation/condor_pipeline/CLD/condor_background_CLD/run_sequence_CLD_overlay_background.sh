#!/bin/bash

HOMEDIR=${1}
GUNCARD=${2}
NEV=${3}
SEED=${4}
OUTPUTDIR=${5}

DIR="/eos/experiment/fcc/ee/datasets/CLD_tracking/condor/Pythia/CLD_background_overlay/"
mkdir ${DIR}
mkdir ${DIR}${SEED}
cd ${DIR}${SEED}

SAMPLE="Zcard_CLD"


cp -r /afs/cern.ch/work/m/mgarciam/private/CLD_Config_versions/CLDConfig_230924_background/CLDConfig/* .

cp /afs/cern.ch/work/m/mgarciam/private/Tracking_wcoc/data_creation/condor_background_CLD/runOverlayTiming.py .
cp /afs/cern.ch/work/m/mgarciam/private/Tracking_wcoc/data_creation/condor_background_CLD/make_pftree_clic_bindings.py .
cp /afs/cern.ch/work/m/mgarciam/private/Tracking_wcoc/data_creation/condor_background_CLD/tree_tools.py .

if [[ "${SAMPLE}" == "Zcard_CLD" ]]
      then 
      cp ${HOMEDIR}/Pythia_generation/${SAMPLE}.cmd card.cmd
      echo "Random:seed=${SEED}" >> card.cmd
      # cat card.cmd
      cp ${HOMEDIR}/Pythia_generation/pythia.py ./
fi


wrapperfunction() {
     source /cvmfs/sw-nightlies.hsf.org/key4hep/setup.sh  
}
wrapperfunction


if [[ "${SAMPLE}" == "Zcard_CLD" ]]
then
      k4run pythia.py -n $NEV --Dumper.Filename out.hepmc --Pythia8.PythiaInterface.pythiacard card.cmd
fi
 

ddsim --compactFile $K4GEO/FCCee/CLD/compact/CLD_o2_v06/CLD_o2_v06.xml --outputFile out_sim_edm4hep.root \
 --steeringFile cld_steer.py --inputFiles out.hepmc --numberOfEvents ${NEV} --random.seed ${SEED}


k4run runOverlayTiming.py

k4run CLDReconstruction.py -n ${NEV}  --inputFiles output_overlay_new1.root --outputBasename out_reco_edm4hep


python make_pftree_clic_bindings.py out_reco_edm4hep_REC.edm4hep.root tree.root True False

mkdir -p ${OUTPUTDIR}
python /afs/cern.ch/work/f/fccsw/public/FCCutils/eoscopy.py tree.root ${OUTPUTDIR}/pf_tree_${SEED}.root

