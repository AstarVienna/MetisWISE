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
apt-file update

conda activate base
conda update -y -n base -c defaults conda
