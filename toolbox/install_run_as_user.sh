#!/usr/bin/env bash

# https://betterdev.blog/minimal-safe-bash-script-template/
set -Eeuo pipefail

# TODO: Make sure it isn't a problem when commands from the Dockerfile are repeated
#conda config --add channels defaults
#conda config --add channels conda-forge
#conda config --add channels omegacen
# TODO: set credentials
#conda config --add channels "https://${OMEGACEN_CONDA_CREDENTIALS}@conda.astro-wise.org/"
#
## TODO: Activate environment, now everything must be done as root.
##conda create -n metiswise
##conda activate metiswise
#
## https://stackoverflow.com/a/78293971
#conda install -y --solver=classic conda-forge::conda-libmamba-solver conda-forge::libmamba conda-forge::libmambapy conda-forge::libarchive
#
## Install dependencies
## psycopg2 for PostgreSQL connection
#conda install -y common psycopg2 astropy pytest jupyter httpcore lxml httpx docutils pooch scipy

# TODO: use a conda environment
conda activate base

cd "${HOME}"

git clone https://github.com/AstarVienna/ScopeSim.git
pushd ScopeSim
pip install -e .
popd

git clone https://github.com/AstarVienna/ScopeSim_Templates.git
pushd ScopeSim_Templates
pip install -e .
popd

git clone https://github.com/AstarVienna/ScopeSim_Data.git
pushd ScopeSim_Data
pip install -e .
popd

git clone https://github.com/AstarVienna/METIS_DRLD.git
pushd METIS_DRLD
pip install -e .
popd

git clone -b jb/ifu_rsrf https://github.com/AstarVienna/METIS_Simulations.git
pushd METIS_Simulations
pip install -e .
popd

git clone https://github.com/AstarVienna/METIS_Pipeline.git
bash "${HOME}/METIS_Pipeline/toolbox/create_config.sh"

git clone https://github.com/AstarVienna/irdb.git

git clone https://github.com/AstarVienna/METIS_Pipeline_Test_Data.git

# TODO: check whether directory already exists.
#git clone https://github.com/AstarVienna/MetisWISE.git
pushd MetisWISE
pip install -e .
popd

echo "export AWETARGET=metiswise" >> "${HOME}/.bashrc"
echo 'eval "$(conda shell.bash hook)"' >> "${HOME}/.bashrc"
echo "conda activate base" >> "${HOME}/.bashrc"
