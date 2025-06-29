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
mkdir -p "${HOME}/space/control/"
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

ln -s irdb inst_pkgs

# Do one run with just img.yaml with nCores==1, because
# setting nCores to 10 or so can cause troubles with pooch because it will
# try to download the same file twice at the same time.
YAML="$DIR_SIMULATIONS/YAML/img.yaml"
python3 "${DIR_SIMULATIONS}/python/run_recipes.py" \
    --inputYAML="${YAML}" \
    --outputDir "${HOME}/space/raw" \
    --doCalib=1 --sequence=1 --doStatic --nCores=1

#YAML="$DIR_SIMULATIONS/YAML/allRecipes.yaml"
#python3 "${DIR_SIMULATIONS}/python/run_recipes.py" \
#    --inputYAML="${YAML}" \
#    --outputDir "${HOME}/space/raw" \
#    --doCalib=1 --sequence=1 --doStatic --nCores=10

echo "Classify data with the EDPS"
edps -w metis.metis_wkf -i "${HOME}/space/raw" -c

echo "Ingesting raw data into the archive"
python MetisWISE/metiswise/tools/ingest_file.py space/raw/*.fits

echo "Process data with the EDPS"
edps -w metis.metis_wkf -i "${HOME}/space/raw" -o "${HOME}/space/processed"
# TODO: figure out how to move the files.

echo "Ingesting processed data into the archive"
# TODO: These filenames are not unique at all, so this won't work as intended.
python MetisWISE/metiswise/tools/ingest_file.py /tmp/EDPS_data/METIS/metis_det_dark/9e3f255c-03af-4ab2-aa1c-2009cc77d941/MASTER_DARK_2RG.fits

echo "Stay a while... stay forever!"
while true; do sleep 60 ; done
