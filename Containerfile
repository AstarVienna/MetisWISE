# Usage:
#
# 1) Get OMEGACEN_CONDA_CREDENTIALS from https://metis.strw.leidenuniv.nl/wiki/doku.php?id=ait:archive
# export OMEGACEN_CONDA_CREDENTIALS=username:password
#
# 2) Build the image
# podman build --secret=id=OMEGACEN_CONDA_CREDENTIALS,type=env -t metiswise .
#
# 3) Run the image
# podman run  -it --network=host --volume="/:/hostroot" --volume="${XAUTHORITY:-$HOME/.Xauthority}:/home/metis/.Xauthority:ro"   --env DISPLAY="${DISPLAY}" metiswise

FROM quay.io/condaforge/miniforge3:25.3.0-3

MAINTAINER Hugo Buddelmeijer <hugo@buddelmeijer.nl>

# Run-time dependencies:
# -
#
# Build dependencies:
# - conda-build
#
# Development dependencies:
# -
#
# Optional dependencies for convenience:
# - x11-apps: for xclock to test X11 connection
# - emacs: to use as EDITOR
# - file less curl vim man-db meld tmux apt-file inetutils-ping

# See install_dependencies_debian.sh for these commands.
# They are repeated here to allow podman to cache layers.
RUN \
    apt-get update; \
    apt-get upgrade -y; \
    apt-get install -y file less emacs curl vim man-db meld tmux apt-file x11-apps inetutils-ping; \
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
        emacs vim nano; \
    apt-file update;

RUN --mount=type=secret,id=OMEGACEN_CONDA_CREDENTIALS \
    conda config --add channels conda-forge; \
    conda config --add channels omegacen; \
    conda config --add channels "https://$(cat /run/secrets/OMEGACEN_CONDA_CREDENTIALS)@conda.astro-wise.org/"; \
    conda install -y common psycopg2 cpl python-cpl metiswise;

# Setting CPLDIR is necessary to install pycpl
ENV CPLDIR=/opt/conda

RUN pip install \
    --extra-index-url https://ftp.eso.org/pub/dfs/pipelines/libraries \
    pycpl pyesorex edps adari_core


# TODO: Remove @hb/removetemporaryfiles branch from METIS_Simulations
RUN pip install \
    ScopeSim \
    ScopeSim_Templates \
    git+https://github.com/AstarVienna/ScopeSim_Data.git \
    git+https://github.com/AstarVienna/METIS_DRLD.git \
    git+https://github.com/AstarVienna/METIS_Simulations.git@hb/removetemporaryfiles

RUN git clone https://github.com/AstarVienna/METIS_Pipeline.git; \
    bash "${HOME}/METIS_Pipeline/toolbox/create_config.sh"; \
    git clone https://github.com/AstarVienna/irdb.git; \
    echo "export AWETARGET=metiswise" >> "${HOME}/.bashrc"


ENV PYESOREX_PLUGIN_DIR "/root/METIS_Pipeline/metisp/pymetis/src/pymetis/recipes"
ENV PYCPL_RECIPE_DIR "/root/METIS_Pipeline/metisp/pyrecipes/"
ENV PYTHONPATH "/root/METIS_Pipeline/metisp/pymetis/src/"

ENV SOF_DATA "/root/METIS_Pipeline_Test_Data/metis_sim_small_1/data"
ENV SOF_DIR "/root/METIS_Pipeline_Test_Data/metis_sim_small_1/sof"
