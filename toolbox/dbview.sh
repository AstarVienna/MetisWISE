#!/bin/sh
#
# Script for starting and stopping an (Astro-)WISE Http(s) Server, for example DbView
#
# Below are the instructions to setup an WISE HTTP server
#
# The instructions below assume the following;
#
# a. name of the web service <servicename>, for example dbview-astro
# b. web service working directory <servicedir>, default this is the AWEVERSION (so develop, master, ..)
# c. a working WISE installation in /dir/to/awehome
#
# Below the environment variable AWEPIPE is used, to find the default value of this variable :
#
#    awe -c 'import os; print os.environ["AWEPIPE"]'
#
# 1. Copy this script to ${HOME}/bin/<servicename>.sh
#    And define at least the "AWEHOME" and "AWETARGET" variables
#    Optional define "AWEVERSION" and "workdir"
#    To use non default code specify "AWEPIPE" variable

export database_tablespacename="pg_default"
export database_engine="postgresql"
export database_port="5432"
export database_name="postgres/wise"
export database_user="system"
export database_password="klmn"
export ask_administrator_password=""

export database_tablespacename="pg_default"
export database_engine="postgresql"
export database_port="5432"
export database_name="postgres/wise"
export database_user="AWTEST"
export database_password="lmno"
export ask_administrator_password="True"

# 2. Setup the http config file, the config file can be copied from
#
#        cp ${AWEPIPE}/common/services/general/HttpServer.cfg <servicedir>/<servicename>.cfg
#
#    and edit the config file, documentation is contained in the config file.
#
#    These variables should be configured :
#      bindaddr  the address to bind to, for example dbview.astro-wise.org
#      port      the port to listen on, for example 8080
#      domain    the domain of the service, for example astro-wise.org
#      server    the server name, for example dbview
#      allowed1  the directories or files which are allowed to serve, specify multiple by adding allowed2, etc ..
#
# 3. Setup the AWE config file: ${HOME}/.awe/Environment.cfg
#    This should contain at least the credentials, example :
#
#    [global]
#    database_user       : AWANONYMOUS
#    database_password   : ANONYMOUS
#
#    See ${AWEPIPE}/common/config/Environment.cfg and optional
#    ${AWEPIPE}/${AWETARGET}/config/Environment.cfg for all config options
#
# 4. Script usage :
#
#    The script must be called with either
#
#    start   start the service
#    stop    stop the service
#    status  show the status (up/down) of the service
#
#    To start the service :
#      <servicename>.sh start
#
#    The created log file should end like :
#      ....
#      Starting forever http server on <host>:<port>
#      time started 2016-05-19 12:04:07.321478
#      version @(#)$Revision$
#
#    And the web service should be reachable via
#      http://<host>:<port>
#
#
# WJ Vriend (wjvriend AT astro DOT rug DOT nl)
#

# exit script on any error
set -e

####################################
# 1. These variables must be defined

# Path to awehome, the root directory of the WISE installation
#AWEHOME="/repos/wise"
AWEHOME="/opt/conda/lib/python3.11/site-packages"

# Example: common, astro, awlofar, micro, ai, muse, ..
AWETARGET="metiswise"
export AWETARGET

###########################################################
# 2. These variables should be looked at, but have defaults

# Name of the service
# Get the basename of this script, discarding stuff after a possible dot
service="`basename $0 | awk -F. '{print $1}'`"

# The AWE VERSION or CVS tag : develop, master (used to be: current, AWBASE)
#AWEVERSION="develop"
#export AWEVERSION

# The directory with the common and specific (ie astro/muse/...) python code
#AWEPIPE="${AWEHOME}/${AWEVERSION}"
#AWEPIPE="/repos/wise"
AWEPIPE="/opt/conda/lib/python3.11/site-packages"
export AWEPIPE

# Full path to awe client, just use "awe" if awe is in ${PATH}
#AWELINUX=${AWEHOME}/`python ${AWEPIPE}/common/util/targetplatform.py`
#awe="${AWELINUX}/${AWEVERSION}/${AWETARGET}/bin/awe"
awe="python"

# The work dir
#workdir="${HOME}/${AWEVERSION}"
workdir="${HOME}/dbviewtest"

# The (Oracle) instant client version
instantclient="instantclient_11_2"

########################################################
# 3. These variables have defaults, but could be changed

# Extra env variables, define as "key1=value2 key2=value2 ..."
extra_env=""

# Name of the config file
#config="${service}.cfg"
#config="${HOME}/bin/dbview.cfg"
config="${HOME}/MetisWISE/toolbox/dbview.cfg"

# Name of the log file
log="${service}.log"
pid="${service}.pid"

#######################
# 4. Internal variables

# The full env command, these variables are standard set:
# PYTHONSTARTUP - can interfer with the startup of awe, unset
# PYTHONUNBUFFERED - log message going through STDOUT or STDERR can get lost in forked processes
# LD_LIBRARY_PATH - the Oracle instant client is not always found
env="env -u PYTHONSTARTUP PYTHONUNBUFFERED=x LD_LIBRARY_PATH=${AWELINUX}/${instantclient} ${extra_env}"
# The command to start the service
service_cmd="${awe} ${AWEPIPE}/common/services/general/myHttpServer.py -c ${config}"

if [ ! -d "${workdir}" ]; then
    echo "work dir ${workdir} does not exist, creating ... probably a cfg needs to be created, see example in common/services/general/HttpServer.cfg"
    mkdir -p "${workdir}"
fi
cd "${workdir}"

############################
# 5. Arguments of the script

archivelog ()
{
    if [ -f "${log}" ] ; then
        mv "${log}" "${log}.`date +%FT%T`.save"
    fi
}

usage ()
{
    echo "Usage: $1 (start|stop|restart|status)"
}

start ()
{
    if [ -f ${pid} ] ; then
        echo "pid file ${pid} exists, please first check if service is still running with process id `cat ${pid}`"
    else
        echo "Running ${service} in ${workdir}"
        archivelog
        ${env} ${service_cmd} > ${log} 2>&1 &
        echo $! > ${pid}
    fi
}

status ()
{
    if [ -f ${pid} ] ; then
        echo "Up (pid = `cat ${pid}`)"
    else
        echo "Down"
    fi
}

stop ()
{
    if [ -f ${pid} ] ; then
        echo "Stopping service ${service} with pid `cat ${pid}`"
        kill `cat ${pid}`
        rm -f ${pid}
    fi
    archivelog
}

case $1 in
start)
    start
    ;;
status)
    status
    ;;
stop)
    stop
    ;;
restart)
    stop
    sleep 1
    start
    ;;
*)
    usage
    ;;
esac

