#!/usr/bin/env bash
# For some reason .bashrc is skipped.
eval "$(conda shell.bash hook)"
# TODO: use an actual environment
conda activate base
export AWETARGET=metiswise
# TODO: Move to src directory?
export PYTHONPATH="${HOME}/MetisWISE"
"${HOME}/MetisWISE/toolbox/dbview.sh" start

echo "Sleeping to keep the container running"
while true; do sleep 60 ; done
