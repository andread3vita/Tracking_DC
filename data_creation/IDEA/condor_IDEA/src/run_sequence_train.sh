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

OUTDIR=/eos/experiment/fcc/ee/datasets/DC_tracking/Pythia/
PFDIR=/afs/cern.ch/work/m/mgarciam/private/Tracking_wcoc
NEV=100
GUNCARD="config.gun"
NUM=${1} #random seed
#SAMPLE="Zcard" #main card
SAMPLE="gun" #main card



WORKDIR=/eos/experiment/fcc/ee/datasets/DC_tracking/Pythia/scratch/${SAMPLE}/${NUM}/
FULLOUTDIR=${OUTDIR}/${SAMPLE}
PATH_TO_K4GEO="/afs/cern.ch/work/m/mgarciam/private/k4geo"
K4RECTRACKER_dir="/afs/cern.ch/work/m/mgarciam/private/k4RecTracker"
mkdir -p $FULLOUTDIR

mkdir $WORKDIR
cd $WORKDIR

# cp $PFDIR/Pythia_generation/${SAMPLE}.cmd card.cmd
cp $PFDIR/Pythia_generation/pythia.py ./
cp -r $PFDIR/gun/gun_random_angle.cpp .
cp -r $PFDIR/gun/compile_gun_RA.x .
cp $PFDIR/data_processing/process_tree.py ./
cp $PFDIR/data_processing/tools_tree.py ./
cp $K4RECTRACKER_dir/runIDEAtrackerDigitizer.py ./
cp -r $PFDIR/gun/${GUNCARD} .

# echo "Random:seed=${NUM}" >> card.cmd
# cat card.cmd
## gun 
source compile_gun_RA.x
echo 'nevents '${NEV} >> ${GUNCARD}
./gun ${GUNCARD} 


## pythia
source /cvmfs/sw-nightlies.hsf.org/key4hep/setup.sh

k4run $PFDIR/Pythia_generation/pythia.py -n $NEV --Dumper.Filename out.hepmc --Pythia8.PythiaInterface.pythiacard card.cmd

ddsim --compactFile $PATH_TO_K4GEO/FCCee/IDEA/compact/IDEA_o1_v02/IDEA_o1_v02.xml \
      --outputFile out_sim_edm4hep.root \
      --inputFiles out.hepmc \
      --numberOfEvents $NEV \
      --random.seed $NUM \
      --part.minimalKineticEnergy "0.001*MeV" \

cd $K4RECTRACKER_dir
export K4RECTRACKER=$PWD/install/share/; PATH=$PWD/install/bin/:$PATH; CMAKE_PREFIX_PATH=$PWD/install/:$CMAKE_PREFIX_PATH; LD_LIBRARY_PATH=$PWD/install/lib:$PWD/install/lib64:$LD_LIBRARY_PATH; export PYTHONPATH=$PWD/install/python:$PYTHONPATH
cd $WORKDIR
k4run runIDEAtrackerDigitizer.py

python process_tree.py output_IDEA_DIGI.root reco_${SAMPLE}_${NUM}.root 

cp reco_${SAMPLE}_${NUM}.root $FULLOUTDIR/