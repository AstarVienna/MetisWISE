#!/usr/bin/env bash

# https://betterdev.blog/minimal-safe-bash-script-template/
set -Eeuo pipefail


apt-get update
apt-get upgrade -y

# It is necessary to install emacs to ensure that the figures are consistently
# created. This is probably due to the font related packages that are
# installed as a dependency.
# curl is necessary to download some files. The rest is just useful.
apt-get install -y file less emacs curl vim man-db meld tmux apt-file x11-apps inetutils-ping
apt-get install -y \
    build-essential \
    pkg-config \
    wget gcc  automake autogen libtool gsl-bin libgsl-dev libfftw3-bin libfftw3-dev fftw-dev \
    curl bzip2 less subversion git cppcheck lcov valgrind \
    zlib1g zlib1g-dev \
    liberfa1 liberfa-dev \
    libcurl4-openssl-dev libcurl4 \
    tmux ripgrep file \
    libcfitsio-bin libcfitsio-dev \
    wcslib-dev wcslib-tools \
    perl cmake \
    graphviz meld \
    emacs vim nano
apt-file update

conda activate base
conda update -y -n base -c defaults conda
