#!/usr/bin/env bash
set -Eeuo pipefail

echo "Setting up MetisWISE test system."

echo "Become system user"
source "${HOME}/MetisWISE/toolbox/become_system_user.sh"

while true ; do
  if psql "postgres://${database_user}:${database_password}@${database_name}" -p "${database_port}" -c "select version();" -x ; then
    echo "Database found!"
    break
  fi
  echo "Database not yet found, sleeping."
  sleep 1
done

echo "Setup database"
python "${HOME}/MetisWISE/metiswise/tools/dbtestsetup.py"

echo "Become normal user again"
source "${HOME}/MetisWISE/toolbox/become_normal_user.sh"

echo "Tell the dbviewer it can start"
touch "${HOME}/space/control/database_setup"

echo "Can we run recipes?"
pyesorex --recipes

echo "Starting the edps by listing workflows"
# Need to start the edps in the right directory, because the workflow_dir
# is listed as .
pushd METIS_Pipeline
edps -lw
popd

echo "Going to simulate some data"
DIR_SITE_PACKAGES=$(python -c "from distutils.sysconfig import get_python_lib; print(get_python_lib())")
DIR_SIMULATIONS="${DIR_SITE_PACKAGES}/Simulations"
# YAML="$DIR_SIMULATIONS/YAML/allRecipes.yaml"
YAML="$DIR_SIMULATIONS/YAML/img.yaml"

ln -s irdb inst_pkgs
# TODO: Ensure nCores can be set to 10 or so; can cause troubles with pooch.
python3 "${DIR_SIMULATIONS}/python/run_recipes.py" \
    --inputYAML="${YAML}" \
    --outputDir "${HOME}/space/raw" \
    --doCalib=1 --sequence=1 --doStatic --nCores=1

echo "Classify data with the EDPS"
edps -w metis.metis_wkf -i "${HOME}/space/raw" -c

echo "Process data with the EDPS"
edps -w metis.metis_wkf -i "${HOME}/space/raw" -o "${HOME}/space/processed"
# TODO: figure out how to move the files.

echo "Stay a while... stay forever!"
while true; do sleep 60 ; done
