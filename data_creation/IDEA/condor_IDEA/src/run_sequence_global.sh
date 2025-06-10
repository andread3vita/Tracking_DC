#!/bin/bash
# the code comes from here: https://zenodo.org/records/8260741
#SBATCH -p main
#SBATCH --mem-per-cpu=6G
#SBATCH --cpus-per-task=1
#SBATCH -o logs/slurm-%x-%j-%N.out
# set -e
# set -x

# env
# df -h

OUTDIR=${1} 
TYPE=${2} 
CONFIG=${3} 
VERSION=${4} 
OPTION=${5} 
SEED=${6} #random seed
NEV=500

PFDIR=/afs/cern.ch/user/a/adevita/public/workDir/Tracking_DC/data_creation
WORKDIR=${OUTDIR}/${TYPE}/temp/
FULLOUTDIR=${OUTDIR}/${TYPE}/${CONFIG}

mkdir -p $WORKDIR

PATH_TO_K4GEO="/eos/user/a/adevita/saveSpace/k4geo"
K4RECTRACKER_dir="/eos/user/a/adevita/saveSpace/k4RecTracker"

sleep 5
echo ""
echo "Sourcing k4RecTracker setup.sh"

ORIG_PARAMS=("$@")
set --
cd $K4RECTRACKER_dir
source setup.sh
k4_local_repo
set -- "${ORIG_PARAMS[@]}"
echo ""

ORIG_PARAMS=("$@")
set --
cd $PATH_TO_K4GEO
k4_local_repo
set -- "${ORIG_PARAMS[@]}"
echo ""

cd $WORKDIR
mkdir -p out_hepmc/
if [[ "${TYPE}" == "Pythia" ]]
      then 
      cp $PFDIR/Pythia_generation/${CONFIG}.cmd ${CONFIG}_${SEED}.cmd
      echo "Random:seed=${SEED}" >> ${CONFIG}_${SEED}.cmd

      k4run $PFDIR/Pythia_generation/pythia.py -n $NEV --Dumper.Filename out_hepmc/out_${SEED}.hepmc --Pythia8.PythiaInterface.pythiacard ${CONFIG}_${SEED}.cmd


      rm ${CONFIG}_${SEED}.cmd

      mkdir -p out_edm4hep/
      
      if [[ $VERSION -eq 3 ]]
      then
            ddsim --compactFile $K4GEO/FCCee/IDEA/compact/IDEA_o${OPTION}_v0${VERSION}/IDEA_o${OPTION}_v0${VERSION}.xml \
                  --outputFile out_edm4hep/out_sim_edm4hep_${SEED}.root \
                  --inputFiles out_hepmc/out_${SEED}.hepmc \
                  --numberOfEvents $NEV \
                  --random.seed $SEED \
                  --part.minimalKineticEnergy "0.001*MeV" \
                  --steeringFile  $K4RECTRACKER_dir/SteeringFile_IDEA_o${OPTION}_v0${VERSION}.py
      else
            ddsim --compactFile $K4GEO/FCCee/IDEA/compact/IDEA_o${OPTION}_v0${VERSION}/IDEA_o${OPTION}_v0${VERSION}.xml \
                  --outputFile out_edm4hep/out_sim_edm4hep_${SEED}.root \
                  --inputFiles out_hepmc/out_${SEED}.hepmc \
                  --numberOfEvents $NEV \
                  --random.seed $SEED \
                  --part.minimalKineticEnergy "0.001*MeV"
      fi
      rm out_hepmc/out_${SEED}.hepmc

      mkdir -p out_digi/
      k4run ${K4RECTRACKER_dir}/runIDEAv${VERSION}TrackerDigitizer.py --inputFile out_edm4hep/out_sim_edm4hep_${SEED}.root --outputFile out_digi/output_IDEA_DIGI_${SEED}.root
      rm out_edm4hep/out_sim_edm4hep_${SEED}.root

      mkdir -p ${FULLOUTDIR}
      python $PFDIR/data_processing/IDEAv${VERSION}/process_tree_global.py out_digi/output_IDEA_DIGI_${SEED}.root ${FULLOUTDIR}/${CONFIG}_graphs_${SEED}.root False #${DETECTOR} 
      # rm out_digi/output_IDEA_DIGI_${SEED}.root

fi


