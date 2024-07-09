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

OUTDIR=/afs/cern.ch/user/a/adevita/public/workDir/dataset
PFDIR=/afs/cern.ch/user/a/adevita/public/workDir/Tracking_DC/data_creation/
WORKDIR=/afs/cern.ch/user/a/adevita/public/workDir/temp/

NUM=${1}     # random seed
SAMPLE=${2}  # sample
CONFIG=${3}  # configuration file
NEV=${4}     # number of events

echo "Simulation has started"
echo "Random:seed = ${NUM}"
echo "Sample = ${SAMPLE}"
echo "Workdir = ${WORKDIR}"
echo "ConfigFile = ${CONFIG}.gun"

FULLOUTDIR="${OUTDIR}/${CONFIG}/"
PATH_TO_K4GEO="/afs/cern.ch/user/a/adevita/public/workDir/k4geo/"
K4RECTRACKER_dir="/afs/cern.ch/user/a/adevita/public/workDir/k4RecTracker/"
# SOURCEFILE_K4RECTRACKER="/afs/cern.ch/user/a/adevita/public/workDir/k4RecTracker/setup.sh"

mkdir -p $FULLOUTDIR
mkdir -p $WORKDIR

sleep 5
echo ""
echo "Sourcing k4RecTracker setup.sh"

ORIG_PARAMS=("$@")
set --
cd $K4RECTRACKER_dir
source setup.sh
k4_local_repo
cd $WORKDIR
set -- "${ORIG_PARAMS[@]}"
echo ""

TEMP_OUT="out_${SAMPLE}_${NUM}.hepmc"
if [[ "${SAMPLE}" == "gun" ]] 
then 
      cp -r $PFDIR/gun/gun_random_angle.cpp .
      cp -r $PFDIR/gun/CMakeLists.txt .
      cp -r $PFDIR/gun/gun.cpp .
      cp -r "$PFDIR/gun/configurations/${CONFIG}.gun" .

      echo "" >> $CONFIG.gun
      echo "nevents ${NEV}" >> $CONFIG.gun
      echo "  "
      echo " ================================================================================ "
      echo "  "
      echo "running gun"
      echo "  "
      echo " ===============================================================================  "
      echo "  "

      mkdir -p build install
      cd build
      cmake .. -DCMAKE_INSTALL_PREFIX=../install
      make install -j 8
      cd ..
      ./build/gun ${CONFIG}.gun ${TEMP_OUT}

fi 

if [[ "${SAMPLE}" == "Zcard" ]]
      then 
      cp $PFDIR/Pythia_generation/${SAMPLE}.cmd card.cmd
      echo "Random:seed=${NUM}" >> card.cmd


      cp $PFDIR/Pythia_generation/pythia.py ./

      k4run $PFDIR/Pythia_generation/pythia.py -n $NEV --Dumper.Filename $TEMP_OUT --Pythia8.PythiaInterface.pythiacard card.cmd
fi

sleep 5
DDSIM_OUT="out_sim_edm4hep_${SAMPLE}_${NUM}.root"

echo ""
echo ""
echo "Object name = ${TEMP_OUT}"
echo "ddsim output = ${DDSIM_OUT}"
echo ""

echo "Running ddsim"
ddsim --compactFile $PATH_TO_K4GEO/FCCee/IDEA/compact/IDEA_o1_v02/IDEA_o1_v02.xml \
      --outputFile $DDSIM_OUT \
      --inputFiles $TEMP_OUT \
      --numberOfEvents $NEV \
      --random.seed $NUM

sleep 5
echo ""
echo ""
echo "Running digitizer"
cp $K4RECTRACKER_dir/runIDEAtrackerDigitizer.py ./
k4run runIDEAtrackerDigitizer.py --inputFile "out_sim_edm4hep_${SAMPLE}_${NUM}.root" --outputFile "${FULLOUTDIR}/output_IDEA_DIGI_${SAMPLE}_${NUM}.root"

sleep 5
echo ""
echo ""
echo "Running tracker"
mkdir -p "${FULLOUTDIR}eval/"
cp $K4RECTRACKER_dir/runIDEAtracker_eval.py ./
k4run runIDEAtracker_eval.py --inputFile "${FULLOUTDIR}/output_IDEA_DIGI_${SAMPLE}_${NUM}.root" --outputFile "${FULLOUTDIR}eval/output_IDEA_tracking_${SAMPLE}_${NUM}.root"

sleep 5
echo ""
echo ""
echo "Running efficiency computation"
mkdir -p "${FULLOUTDIR}eff/"
cp $K4RECTRACKER_dir/runIDEAtracking_eff.py ./
k4run runIDEAtracker_eval.py --inputFile "${FULLOUTDIR}eval/output_IDEA_tracking_${SAMPLE}_${NUM}.root" --outputFile "${FULLOUTDIR}eff/eff_IDEA_tracking_${SAMPLE}_${NUM}.root"

##### CLEAN
# rm "out_sim_edm4hep_${SAMPLE}_${NUM}.root"
# rm $TEMP_OUT