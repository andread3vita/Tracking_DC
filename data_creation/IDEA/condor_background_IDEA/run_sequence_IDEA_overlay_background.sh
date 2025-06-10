#!/bin/bash

OUTDIR=/eos/experiment/fcc/ee/datasets/DC_tracking/Pythia/
PFDIR=/afs/cern.ch/work/m/mgarciam/private/Tracking_wcoc/data_creation/
NEV=10

NUM=${1} #random seed
SAMPLE="Zcard_CLD" #main card
GEOMETRY_VERSION="IDEA_o1_v03" #main card  #IDEA_o1_v03

HOMEDIR=/afs/cern.ch/work/m/mgarciam/private/Tracking_wcoc/data_creation
WORKDIR=/eos/experiment/fcc/ee/datasets/DC_tracking/Pythia/scratch/${SAMPLE}_background_${GEOMETRY_VERSION}/${NUM}/
echo $WORKDIR
FULLOUTDIR=${OUTDIR}/${SAMPLE}_background_${GEOMETRY_VERSION}/
PATH_TO_K4GEO="/afs/cern.ch/work/m/mgarciam/private/k4geo_versions/k4geo_060125"
K4RECTRACKER_dir="/afs/cern.ch/work/m/mgarciam/private/k4RecTracker_dev_0"
mkdir -p $FULLOUTDIR

mkdir $WORKDIR
cd $WORKDIR
if [[ "${GEOMETRY_VERSION}" == "IDEA_o1_v02" ]]
then
      cp /afs/cern.ch/work/m/mgarciam/private/Tracking_wcoc/data_creation/condor_background_IDEA/runOverlayTiming.py .
fi

if [[ "${GEOMETRY_VERSION}" == "IDEA_o1_v03" ]]
then
      cp /afs/cern.ch/work/m/mgarciam/private/Tracking_wcoc/data_creation/condor_background_IDEA/runOverlayTiming_IDEA_o1_v03.py .
fi

cp /afs/cern.ch/work/m/mgarciam/private/Tracking_wcoc/data_creation/condor_background_IDEA/process_tree_global.py .
cp /afs/cern.ch/work/m/mgarciam/private/Tracking_wcoc/data_creation/condor_background_IDEA/tools_tree_global.py .
cp /afs/cern.ch/work/m/mgarciam/private/Tracking_wcoc/data_creation/condor_background_IDEA/runIDEAtrackerDigitizer.py ./

if [[ "${SAMPLE}" == "Zcard_CLD" ]]
      then 
      cp ${HOMEDIR}/Pythia_generation/${SAMPLE}.cmd card.cmd
      echo "Random:seed=${NUM}" >> card.cmd
      # cat card.cmd
      cp ${HOMEDIR}/Pythia_generation/pythia.py ./
fi


wrapperfunction() {
     source /cvmfs/sw-nightlies.hsf.org/key4hep/setup.sh  
}
wrapperfunction


if [[ "${SAMPLE}" == "Zcard_CLD" ]]
then
      k4run $PFDIR/Pythia_generation/pythia.py -n $NEV --Dumper.Filename out.hepmc --Pythia8.PythiaInterface.pythiacard card.cmd
fi

ddsim --compactFile $PATH_TO_K4GEO/FCCee/IDEA/compact/$GEOMETRY_VERSION/$GEOMETRY_VERSION.xml \
      --outputFile out_sim_edm4hep_base.root \
      --inputFiles out.hepmc \
      --numberOfEvents $NEV \
      --random.seed $NUM \
      --part.minimalKineticEnergy "0.001*MeV"
      # --action.tracker Geant4TrackerAction

if [[ "${GEOMETRY_VERSION}" == "IDEA_o1_v02" ]]
then  
      k4run runOverlayTiming.py
fi 

if [[ "${GEOMETRY_VERSION}" == "IDEA_o1_v03" ]]
then  
      k4run runOverlayTiming_IDEA_o1_v03.py
fi 

if [[ "${GEOMETRY_VERSION}" == "IDEA_o1_v02" ]]
then
      cd $K4RECTRACKER_dir
      k4_local_repo
      # # # # # # export K4RECTRACKER=$PWD/install/share/; PATH=$PWD/install/bin/:$PATH; CMAKE_PREFIX_PATH=$PWD/install/:$CMAKE_PREFIX_PATH; LD_LIBRARY_PATH=$PWD/install/lib:$PWD/install/lib64:$LD_LIBRARY_PATH; export PYTHONPATH=$PWD/install/python:$PYTHONPATH
      cd $WORKDIR
      k4run runIDEAtrackerDigitizer.py
      python process_tree_global.py output_IDEA_DIGI.root reco_${SAMPLE}_${NUM}_mc2.root False
      cp reco_${SAMPLE}_${NUM}_mc2.root $FULLOUTDIR/
fi