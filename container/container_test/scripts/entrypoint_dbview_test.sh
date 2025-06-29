#!/usr/bin/env bash

while [ ! -f  /root/space/control/database_setup ]; do
  echo "Database not yet setup, sleeping"
  sleep 1
done

echo "Starting database"
"${HOME}/MetisWISE/toolbox/dbview.sh" start

echo "Sleeping so the script won't quit"
while true ; do sleep 60 ; done
