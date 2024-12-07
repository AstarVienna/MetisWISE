#!/usr/bin/env bash

apt-get update
apt-get upgrade -y
conda update -y -n base -c defaults conda

# It is necessary to install emacs to ensure that the figures are consistently
# created. This is probably due to the font related packages that are
# installed as a dependency.
# curl is necessary to download some files. The rest is just useful.
apt-get install -y file less emacs curl vim man-db meld tmux apt-file x11-apps
apt-file update

conda config --add channels conda-forge
conda config --add channels omegacen
# TODO: set credentials
conda config --add channels "https://${OMEGACEN_CONDA_CREDENTIALS}@conda.astro-wise.org/"

# conda is not able to resolve all the dependencies of MicadoWISE, but the
# drop-in replacement mamba is. boa provides mambabuild, the equivalent of
# conda build.
conda install -y mamba boa
