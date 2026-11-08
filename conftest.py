"""Session fixtures for an optional, disposable MetisWISE database."""

import configparser
from importlib.resources import files
import os
from pathlib import Path
import runpy
import secrets
import sys

import pytest


ROOT = Path(__file__).resolve().parent

# Keep ordinary pytest runs usable without the optional postgres group.
try:
    from pytest_postgresql import factories
except ImportError:
    factories = None

if factories is not None:
    metiswise_postgresql_proc = factories.postgresql_proc(
        host="127.0.0.1",
        user="system",
        password=secrets.token_urlsafe(32),
        dbname="wise",
        postgres_options="-c listen_addresses=127.0.0.1",
    )


def pytest_addoption(parser):
    parser.addoption(
        "--run-postgresql",
        action="store_true",
        help="Run database tests against a temporary local PostgreSQL server",
    )
    parser.addoption(
        "--run-simulations",
        action="store_true",
        help="Run real ScopeSim simulations (also requires --run-postgresql)",
    )
    parser.addoption(
        "--simulation-block",
        action="append",
        default=None,
        help="Installed simulation block to run, e.g. ESO/imgLM; repeat to run several (default: ESO/imgLM)",
    )
    parser.addoption(
        "--run-edps", action="store_true",
        help="Process simulated files with metis_wkf before ingestion (requires --run-simulations)",
    )
    parser.addoption(
        "--edps-input", action="append", default=[],
        help="Additional calibration FITS file or directory for EDPS; may be repeated",
    )
    parser.addoption(
        "--edps-target", action="append", default=None,
        help="Limit metis_wkf to a named task; may be repeated (default: workflow targets)",
    )
    parser.addoption(
        "--edps-timeout", type=float, default=600,
        help="Maximum time in seconds to wait for EDPS jobs (default: 600)",
    )
    parser.addoption(
        "--irdb-root",
        default=None,
        help="Directory containing METIS, ELT and Armazones instrument packages",
    )


def pytest_configure(config):
    if config.getoption("--run-edps") and not config.getoption("--run-simulations"):
        raise pytest.UsageError("--run-edps also requires --run-simulations and --run-postgresql")
    if config.getoption("--run-simulations") and not config.getoption("--run-postgresql"):
        raise pytest.UsageError("--run-simulations also requires --run-postgresql")


def pytest_collection_modifyitems(config, items):
    if not config.getoption("--run-postgresql"):
        skip = pytest.mark.skip(reason="requires --run-postgresql")
        for item in items:
            if "postgresql" in item.keywords:
                item.add_marker(skip)
    if not config.getoption("--run-simulations"):
        skip = pytest.mark.skip(reason="requires --run-simulations")
        for item in items:
            if "simulations" in item.keywords:
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


@pytest.fixture(scope="session")
def metiswise_database(request, tmp_path_factory):
    """Initialize once, before tests import any persistent classes.

    Class registrations survive for the Python session, so the schema must too.
    Tests that commit objects should delete them when finished.
    """
    if not request.config.getoption("--run-postgresql"):
        pytest.skip("requires --run-postgresql")
    if factories is None:
        raise pytest.UsageError("Install the postgres dependency group to run these tests")

    import psycopg

    # Resolve lazily so skipped tests don't start a server or require the plugin.
    server = request.getfixturevalue("metiswise_postgresql_proc")
    with psycopg.connect(
        host=server.host, port=server.port, user=server.user,
        password=server.password, dbname="postgres", autocommit=True,
    ) as connection:
        connection.execute("CREATE DATABASE wise OWNER system")

    directory = tmp_path_factory.mktemp("metiswise")
    # Override personal/inherited settings before importing common's backend.
    defaults = configparser.ConfigParser(interpolation=None)
    common_config = files("common.config").joinpath("Environment.cfg")
    metiswise_config = ROOT / "metiswise/config/Environment.cfg"
    defaults.read([str(common_config), str(metiswise_config)])
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
        database_password=server.password,
        ask_administrator_password="",
        project="SIM (1)",
        data_server="127.0.0.1",
        data_port="8000",
        data_protocol="http",
        log_dir=str(directory),
    )
    with pytest.MonkeyPatch.context() as monkeypatch:
        for key in list(os.environ):
            if key.startswith("AWE"):
                monkeypatch.delenv(key)
        for key, value in settings.items():
            monkeypatch.setenv(key, value)
        try:
            _initialize_database(server)
            yield
        finally:
            _disconnect_database()


def _initialize_database(server):
    """Build the schema as AWOPER, then connect as the normal test user."""
    import psycopg

    runpy.run_module("metiswise.tools.dbtestsetup", run_name="__main__")

    # Setup leaves the connection as AWOPER. Keep its class registrations but
    # switch the connection and defaults to the normal user before testing.
    from common.config.Environment import Env
    from common.config.Profile import profiles
    from common.database.Database import database

    database.disconnect()
    profiles.remove_profile()
    test_password = secrets.token_urlsafe(32)
    with psycopg.connect(
        host=server.host, port=server.port, user=server.user,
        password=server.password, dbname="wise", autocommit=True,
    ) as connection:
        connection.execute(
            psycopg.sql.SQL("ALTER ROLE awtest PASSWORD {}").format(
                psycopg.sql.Literal(test_password)
            )
        )
    Env.update(database_user="AWTEST", database_password=test_password)
    profiles.create_profile()
    database.connect()
