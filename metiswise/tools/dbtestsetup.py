# -*- coding: utf-8 -*-
"""Configure a test database.

Assumes a PostgreSQL database is running with user SYSTEM as administrator.
"""
# on some systems (like GUIX), it is necessary to import zlib before importing psycopg2
# noinspection PyUnresolvedReferences
import zlib
import psycopg2

if __name__ == "__main__":

    from common.config.Profile import profiles
    from common.toolbox.backends.postgresql import dbawoper

    # Configure the database as superuser SYSTEM
    profile = profiles.create_profile(username="system")
    from common.database.Database import database

    # The '-9' does not work on an entirely empty database.
    # TODO: Fix dbawoper.configure_database so it works on both an empty
    #       and non-empty database.
    try:
        dbawoper.configure_database(1, "-9", profile.password)
    except psycopg2.errors.UndefinedObject:
        dbawoper.configure_database(1, -9, profile.password)

    from common.toolbox.backends.postgresql import dbnewuser

    dbnewuser.add_user("AWTEST", "lmno")

    # Create persistent classes as AWOPER, need to reimport the database
    from common.database.Database import database  # noqa

    database.disconnect()
    profiles.remove_profile()
    profiles.create_profile(username="AWOPER")
    database.connect()

    # For these persistent class(es) dbflatremake and dbgrants will be run
    # The import will trigger the table creation
    import metiswise.main.aweimports  # noqa

    from common.toolbox.backends.postgresql import dbflatremake

    dbflatremake.create_and_execute_statements()

    from common.database import Security

    # Create project SIM and make all users member of all projects
    Security.add_project(
        "SIM", description="project with simulations", default_privilages=2
    )
    database.execute_insert(
        "insert into aweprojectusers (projectid, userid, usertype) select id, user_id, 1 from aweprojects, aweusers"
    )

    from common.toolbox.backends.postgresql import dbgrants

    dbgrants.grant()
