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

OUTDIR=/afs/cern.ch/user/a/adevita/public/workDir/test/dataset
PFDIR=/afs/cern.ch/user/a/adevita/public/workDir/Tracking_DC/data_creation/
WORKDIR=/afs/cern.ch/user/a/adevita/public/workDir/test/

NUM=${1}     # random seed
SAMPLE=${2}  # sample
CONFIG=${3}  # configuration file
NEV=${4}     # number of events

FULLOUTDIR="${OUTDIR}/${CONFIG}/"
PATH_TO_K4GEO="/afs/cern.ch/user/a/adevita/public/workDir/k4geo/"
K4RECTRACKER_dir="/afs/cern.ch/user/a/adevita/public/workDir/k4RecTracker/"

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

cd $WORKDIR
mkdir -p "${FULLOUTDIR}out_${SAMPLE}/"
TEMP_OUT="${FULLOUTDIR}out_${SAMPLE}/out_${SAMPLE}_${NUM}.hepmc"


if [[ "${SAMPLE}" == "gun" ]] 
then 
      
      echo "Simulation has started"
      echo "Random:seed = ${NUM}"
      echo "Sample = ${SAMPLE}"
      echo "Workdir = ${WORKDIR}"
      echo "ConfigFile = ${CONFIG}.gun"

      cp -r $PFDIR/gun/gun_random_angle.cpp .
      cp -r $PFDIR/gun/CMakeLists.txt .
      cp -r $PFDIR/gun/gun.cpp .

      cp -r "$PFDIR/gun/configurations/${CONFIG}.gun" .
      echo "" >> $CONFIG.gun
      echo "nevents ${NEV}" >> $CONFIG.gun

      mkdir -p build install
      cd build
      cmake .. -DCMAKE_INSTALL_PREFIX=../install
      make install -j 8

      cd $WORKDIR
      ./build/gun ${CONFIG}.gun $TEMP_OUT $NUM

fi 

if [[ "${SAMPLE}" == "Zcard" ]]
      then 
      
      echo "Simulation has started"
      echo "Random:seed = ${NUM}"
      echo "Sample = ${SAMPLE}"
      echo "Workdir = ${WORKDIR}"
      echo "ConfigFile = ${CONFIG}.cmd"

      cp $PFDIR/Pythia_generation/${SAMPLE}.cmd card.cmd
      echo "Random:seed=${NUM}" >> card.cmd
      cp $PFDIR/Pythia_generation/pythia.py ./

      k4run $PFDIR/Pythia_generation/pythia.py -n $NEV --Dumper.Filename $TEMP_OUT --Pythia8.PythiaInterface.pythiacard card.cmd
fi

sleep 5
DDSIM_OUT="${FULLOUTDIR}out_sim_edm4hep/out_sim_edm4hep_${SAMPLE}_${NUM}.root"

echo ""
echo ""
echo "Object name = ${TEMP_OUT}"
echo "ddsim output = ${DDSIM_OUT}"
echo ""

echo "Running ddsim"
mkdir -p "${FULLOUTDIR}out_sim_edm4hep/"
ddsim --compactFile $PATH_TO_K4GEO/FCCee/IDEA/compact/IDEA_o1_v02/IDEA_o1_v02.xml \
      --outputFile $DDSIM_OUT \
      --inputFiles $TEMP_OUT \
      --numberOfEvents $NEV \
      --random.seed $NUM

sleep 5
echo ""
echo ""
echo "Running digitizer"
cp $K4RECTRACKER_dir/runIDEAdigitizer.py ./
k4run runIDEAdigitizer.py --inputFile $DDSIM_OUT --outputFile "${FULLOUTDIR}/output_IDEA_DIGI_${SAMPLE}_${NUM}.root"

sleep 5
echo ""
echo ""
echo "Running tracker"
mkdir -p "${FULLOUTDIR}eval/"
cp $K4RECTRACKER_dir/runIDEAtracker.py ./
k4run runIDEAtracker.py --inputFile "${FULLOUTDIR}/output_IDEA_DIGI_${SAMPLE}_${NUM}.root" --outputFile "${FULLOUTDIR}eval/output_IDEA_tracking_${SAMPLE}_${NUM}.root"

sleep 5
echo ""
echo ""
echo "Running efficiency computation"
mkdir -p "${FULLOUTDIR}eff/"
if [[ "${SAMPLE}" == "Zcard" ]]
      then 

      cp $K4RECTRACKER_dir/runIDEAtracking_eff_pythia.py ./
      k4run runIDEAtracking_eff_pythia.py --inputFile "${FULLOUTDIR}eval/output_IDEA_tracking_${SAMPLE}_${NUM}.root" --outputFile "${FULLOUTDIR}eff/eff_IDEA_tracking_${SAMPLE}_${NUM}.root"


fi

if [[ "${SAMPLE}" == "gun" ]] 
      then 

      cp $K4RECTRACKER_dir/runIDEAtracking_eff_gun.py ./
      k4run runIDEAtracking_eff_gun.py --inputFile "${FULLOUTDIR}eval/output_IDEA_tracking_${SAMPLE}_${NUM}.root" --outputFile "${FULLOUTDIR}eff/eff_IDEA_tracking_${SAMPLE}_${NUM}.root"

fi


# ##### CLEAN
# rm "${DDSIM_OUT}"
# rm "${TEMP_OUT}"
# rm "${FULLOUTDIR}/output_IDEA_DIGI_${SAMPLE}_${NUM}.root"
# rm "${FULLOUTDIR}eval/output_IDEA_tracking_${SAMPLE}_${NUM}.root"