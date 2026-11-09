#!/bin/bash -l

#SBATCH --job-name=natl
#SBATCH --tasks-per-node=64
#SBATCH --mem=64GB
#SBATCH -t 36:00:00
#=================================================

ulimit
date
time

inmap run steady -s --config="natl.toml"

# show when run finished
date

exit 0
