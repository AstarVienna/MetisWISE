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

# Copy over the repository.
COPY . ${HOME}/MetisWISE

# Install
RUN bash -l ${HOME}/MetisWISE/toolbox/install_dependencies_debian.sh

#USER ${NB_USER}

RUN bash -l ${HOME}/MetisWISE/toolbox/install_run_as_user.sh
