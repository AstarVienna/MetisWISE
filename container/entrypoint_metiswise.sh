#!/usr/bin/env bash
# For some reason .bashrc is skipped.
eval "$(conda shell.bash hook)"
# TODO: use an actual environment
conda activate base
export AWETARGET=metiswise
# TODO: Move to src directory?
export PYTHONPATH="${HOME}/MetisWISE"

# Ensure the database is setup correctly.
source "${HOME}/MetisWISE/toolbox/become_system_user.sh"
python "${HOME}/metiswise/tools/dbtestsetup.py"

# Become normal user again.
source "${HOME}/MetisWISE/toolbox/become_normal_user.sh"
