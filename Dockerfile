# docker build -t metiswise .
#
# docker run  -it --network=host --volume="/mnt/data/hugo/scratch:/scratch" --volume="/mnt/data/hugo/repos:/repos" --volume="${XAUTHORITY:-$HOME/.Xauthority}:/home/metis/.Xauthority:ro"   --env DISPLAY="${DISPLAY}" metiswise

# TODO: Update Python version
# 23.10.0-1 is the last one with Python 3.11
FROM continuumio/miniconda3:23.10.0-1

MAINTAINER Hugo Buddelmeijer <hugo@buddelmeijer.nl>

# User as prescribed in
# https://mybinder.readthedocs.io/en/latest/tutorials/dockerfile.html
ARG NB_USER=metis
# TODO: Somehow put user ID of account that builds this here
ARG NB_UID=1000
ENV USER ${NB_USER}
ENV NB_UID ${NB_UID}
ENV HOME /home/${NB_USER}
RUN adduser --uid ${NB_UID} ${NB_USER}
RUN chown -R ${NB_UID} ${HOME}

# See install_dependencies_debian.sh for these commands.
# They are repeated here to allow docker to cache layers.
RUN apt-get update; \
    apt-get upgrade -y; \
    apt-get install -y file less emacs curl vim man-db meld tmux apt-file x11-apps inetutils-ping; \
    apt-file update;

# TODO: set credentials
RUN conda update -y -n base -c defaults conda; \
    conda config --add channels defaults; \
    conda config --add channels conda-forge; \
    conda config --add channels omegacen; \
    conda config --add channels "https://${OMEGACEN_CONDA_CREDENTIALS}@conda.astro-wise.org/" \
    conda install -y --solver=classic conda-forge::conda-libmamba-solver conda-forge::libmamba conda-forge::libmambapy conda-forge::libarchive; \
    conda install -y common psycopg2 astropy pytest jupyter httpcore lxml httpx docutils pooch scipy;

# Copy over the repository. This breaks the caching.
COPY . ${HOME}/MetisWISE

# Install
#RUN bash -l ${HOME}/MetisWISE/toolbox/install_dependencies_debian.sh

# TODO: Enable NB_USER again
#USER ${NB_USER}

RUN bash -l ${HOME}/MetisWISE/toolbox/install_run_as_user.sh
