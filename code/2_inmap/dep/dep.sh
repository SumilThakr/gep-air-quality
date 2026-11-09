#!/bin/bash -l

#SBATCH --job-name=dep
#SBATCH --tasks-per-node=64
#SBATCH -t 36:00:00
#SBATCH --mem=64GB
#=================================================

ulimit
date
time

inmap run steady -s --config="dep.toml"

# show when run finished
date

exit 0
