#!/bin/bash


NEV=1
SEED=${1}
OUTPUTDIR="/eos/experiment/fcc/ee/datasets/DC_tracking/Pythia/IDEA_background_only/"

DIR="/eos/experiment/fcc/ee/datasets/DC_tracking/Pythia/scratch/IDEA_background_only/"
mkdir ${DIR}
mkdir ${DIR}${SEED}
cd ${DIR}${SEED}

PATH_TO_K4GEO="/afs/cern.ch/work/m/mgarciam/private/k4geo_versions/k4geo"

cp /eos/experiment/fcc/users/b/brfranco/background_files/guineaPig_andrea_June2024_v23_vtx000/data${SEED}/pairs.pairs . 


wrapperfunction() {
     source /cvmfs/sw.hsf.org/key4hep/setup.sh -r 2024-10-03
}
wrapperfunction



ddsim  --compactFile $PATH_TO_K4GEO/FCCee/IDEA/compact/IDEA_o1_v02/IDEA_o1_v02.xml  \
     --outputFile out_sim_edm4hep_background_${SEED}.root \
     --inputFiles pairs.pairs \
     --numberOfEvents ${NEV} --random.seed ${SEED} \
     --part.minimalKineticEnergy "0.001*MeV"

 
cp out_sim_edm4hep_background_${SEED}.root $OUTPUTDIR/