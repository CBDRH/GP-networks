#!/bin/bash
# The master script. Submits a job for each file in the scratch folder

#PBS -j oe

IN_FOLDER=/srv/scratch/ppcs/MBS
OUT_FOLDER=/srv/scratch/ppcs/out
mkdir -p $OUT_FOLDER/blockstates
mkdir -p $OUT_FOLDER/graphs
mkdir -p $OUT_FOLDER/ppcs
mkdir -p $HOME/GPnetworks/logs

cd $IN_FOLDER
for FILENAME in *.csv
do
    CSV_PATH="$IN_FOLDER/$FILENAME"
    export CSV_PATH OUT_FOLDER FILENAME
    echo "Submitting $CSV_PATH..."
    cd $HOME/GPnetworks/logs
    qsub $HOME/GPnetworks/jobs/preprocess.pbs
done

# after this and all child processes are done, run jobs/clean-up.sh
