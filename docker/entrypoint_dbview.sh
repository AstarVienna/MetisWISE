#!/usr/bin/env bash
# For some reason .bashrc is skipped.
eval "$(conda shell.bash hook)"
# TODO: use an actual environment
conda activate base
export AWETARGET=metiswise
# TODO: Move to src directory?
export PYTHONPATH="${HOME}/MetisWISE"
/home/metis/MetisWISE/toolbox/dbview.sh start

echo "Sleep"
sleep 10
echo "Run another bash so the script won't quit"
bash
