"""Initialize a disposable MetisWISE database before test collection."""

import configparser
from contextlib import ExitStack
from importlib.resources import files
import os
from pathlib import Path
import runpy
import secrets
import shutil
import subprocess
import sys
import tempfile

import pytest


ROOT = Path(__file__).resolve().parent


def pytest_addoption(parser):
    parser.addoption(
        "--run-postgresql",
        action="store_true",
        help="Run database tests against a temporary local PostgreSQL server",
    )


def pytest_collection_modifyitems(config, items):
    if not config.getoption("--run-postgresql"):
        skip = pytest.mark.skip(reason="requires --run-postgresql")
        for item in items:
            if "postgresql" in item.keywords:
                item.add_marker(skip)


def _disconnect_database():
    # Also clean up a connection left behind by a partially failed setup.
    module = sys.modules.get("common.database.Database")
    if module is not None:
        from common.config.Profile import profiles

        connection = module.database.connected()
        if connection and not connection.closed:
            module.database.rollback()
        module.database.disconnect()
        profiles.remove_profile()


def pytest_sessionstart(session):
    config = session.config
    if not config.getoption("--run-postgresql"):
        return

    try:
        import psycopg
        import psycopg2  # noqa: F401 -- common's backend still needs this driver
        from port_for import get_port
        from pytest_postgresql.executors import PostgreSQLExecutor
    except ImportError as error:
        raise pytest.UsageError(
            f"Install the postgres dependency group to run these tests: {error}"
        ) from error

    executable = config.getoption("postgresql_exec", default=None) or shutil.which("pg_ctl")
    if not executable:
        try:
            bindir = subprocess.check_output(
                ["pg_config", "--bindir"], text=True, timeout=30
            ).strip()
            executable = str(Path(bindir) / "pg_ctl")
        except (OSError, subprocess.SubprocessError) as error:
            raise pytest.UsageError(
                "Install PostgreSQL or pass --postgresql-exec=/path/to/pg_ctl"
            ) from error

    # Register cleanup before starting anything; it also runs after setup or
    # collection failures. Callbacks run in reverse order.
    resources = ExitStack()
    config.add_cleanup(resources.close)
    directory = Path(
        resources.enter_context(tempfile.TemporaryDirectory(prefix="metiswise-pg-"))
    )
    monkeypatch = pytest.MonkeyPatch()
    resources.callback(monkeypatch.undo)
    administrator_password = secrets.token_urlsafe(32)
    server = PostgreSQLExecutor(
        executable=executable,
        host="127.0.0.1",
        port=get_port(None),
        datadir=str(directory / "data"),
        unixsocketdir=str(directory),
        logfile=str(directory / "postgresql.log"),
        startparams="-w",
        dbname="wise",
        user="system",
        password=administrator_password,
        postgres_options="-c listen_addresses=127.0.0.1",
    )

    def stop_server():
        if (Path(server.datadir) / "postmaster.pid").exists():
            server.stop()

    resources.callback(stop_server)
    server.start()
    with psycopg.connect(
        host=server.host, port=server.port, user=server.user,
        password=administrator_password, dbname="postgres", autocommit=True,
    ) as connection:
        connection.execute("CREATE DATABASE wise OWNER system")

    # Override personal/inherited settings before importing common's backend.
    defaults = configparser.ConfigParser(interpolation=None)
    common_config = files("common.config").joinpath("Environment.cfg")
    metiswise_config = ROOT / "metiswise/config/Environment.cfg"
    defaults.read([str(common_config), str(metiswise_config)])
    for key in list(os.environ):
        if key.startswith("AWE"):
            monkeypatch.delenv(key)
    settings = dict(defaults["global"])
    settings.update(
        AWETARGET="metiswise",
        AWECOMMONCONFIG=str(common_config),
        AWEMETISWISECONFIG=str(metiswise_config),
        database_engine="postgresql",
        database_administrators='["system", "SYSTEM"]',
        database_tablespacename="pg_default",
        database_name=f"{server.host}:{server.port}/wise",
        database_user="system",
        database_password=administrator_password,
        ask_administrator_password="",
        project="SIM (1)",
        data_server="127.0.0.1",
        data_port="8000",
        data_protocol="http",
        log_dir=str(directory),
    )
    for key, value in settings.items():
        monkeypatch.setenv(key, value)

    resources.callback(_disconnect_database)
    runpy.run_module("metiswise.tools.dbtestsetup", run_name="__main__")

    # Setup leaves the connection as AWOPER. Keep its class registrations but
    # switch the connection and defaults to the normal user before collection.
    from common.config.Environment import Env
    from common.config.Profile import profiles
    from common.database.Database import database

    database.disconnect()
    profiles.remove_profile()
    test_password = secrets.token_urlsafe(32)
    with psycopg.connect(
        host=server.host, port=server.port, user=server.user,
        password=administrator_password, dbname="wise", autocommit=True,
    ) as connection:
        connection.execute(
            psycopg.sql.SQL("ALTER ROLE awtest PASSWORD {}").format(
                psycopg.sql.Literal(test_password)
            )
        )
    Env.update(database_user="AWTEST", database_password=test_password)
    profiles.create_profile()
    database.connect()
