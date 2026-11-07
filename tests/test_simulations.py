"""Run the ESO LM imaging block and ingest its real FITS output."""

from collections import Counter
from importlib.resources import as_file, files
import os
from pathlib import Path
import subprocess
import sys

import pytest


pytestmark = [pytest.mark.postgresql, pytest.mark.simulations]
PACKAGES = ("METIS", "ELT", "Armazones")


def _run(command, directory, environment, logfile):
    """Keep verbose simulator output available on failure, without filling CI logs."""
    with logfile.open("w") as output:
        try:
            result = subprocess.run(
                command, cwd=directory, env=environment, stdout=output,
                stderr=subprocess.STDOUT, timeout=600, check=False,
            )
        except subprocess.TimeoutExpired:
            pytest.fail(f"Simulation command timed out; see {logfile}", pytrace=False)
    if result.returncode:
        pytest.fail(
            f"Simulation command failed ({result.returncode}); see {logfile}\n"
            + logfile.read_text()[-8000:],
            pytrace=False,
        )


@pytest.fixture(scope="session")
def img_lm_files(request, tmp_path_factory):
    """Run the actual script in isolation, using its unchanged ESO YAML inputs."""
    try:
        resources = files("metis_simulations")
    except ModuleNotFoundError as error:
        raise pytest.UsageError("Install the simulations dependency group to run this test") from error
    for relative in ("simulationBlocks/ESO/imgLM.py", "YAML/ESO/scienceLM.yaml", "YAML/ESO/stdLM.yaml"):
        if not resources.joinpath(relative).is_file():
            raise pytest.UsageError(
                f"Installed metis-simulations is missing {relative}; upgrade to a release with bundled resources"
            )

    directory = tmp_path_factory.mktemp("img-lm")
    environment = os.environ.copy()
    environment.update(
        MSIM_NCORES="1", MSIM_OUTDIR=str(directory / "output"), MPLBACKEND="Agg",
    )
    configured_irdb = request.config.getoption("--irdb-root") or os.environ.get("DEFAULT_IRDB_LOCATION")
    local_irdb = Path(__file__).resolve().parents[2] / "irdb"
    if configured_irdb:
        irdb = Path(configured_irdb).expanduser().resolve()
    elif all((local_irdb / package).is_dir() for package in PACKAGES):
        irdb = local_irdb
    else:
        irdb = directory / "inst_pkgs"
        _run(
            [sys.executable, "-c",
             "import scopesim, sys; scopesim.download_packages(sys.argv[2:], save_dir=sys.argv[1])",
             str(irdb), *PACKAGES],
            directory, environment, directory / "download.log",
        )
    for relative in ("METIS/default.yaml", "ELT/ELT.yaml", "Armazones/Armazones.yaml"):
        if not (irdb / relative).is_file():
            raise pytest.UsageError(f"Missing {relative} in IRDB directory {irdb}")
    environment["DEFAULT_IRDB_LOCATION"] = str(irdb)
    with as_file(resources.joinpath("YAML", "ESO")) as yaml_root:
        environment["MSIM_YAML_DIR"] = str(yaml_root)
        _run(
            [sys.executable, "-m", "metis_simulations", "ESO/imgLM", "--small", "--nCores", "1"],
            directory, environment, directory / "simulation.log",
        )
        filenames = sorted((directory / "output").rglob("*.fits"))
        assert filenames, f"imgLM.py produced no FITS files; see {directory / 'simulation.log'}"
        yield filenames, yaml_root



def test_img_lm_files_can_be_ingested(img_lm_files, metiswise_database):
    from astropy.io import fits
    import yaml

    # Import persistent classes only after the database fixture has initialized.
    from common.database.Context import context
    from common.database.Database import database
    from metiswise.main.raw import Raw
    from metiswise.tools.ingest_file import ingest_file

    filenames, yaml_root = img_lm_files
    expected = Counter()
    for name in ("scienceLM.yaml", "stdLM.yaml"):
        recipes = yaml.safe_load((yaml_root / name).read_text())
        for recipe in recipes.values():
            props = recipe["properties"]
            expected[(props["catg"], props["tech"], props["type"])] += props["nObs"]

    assert len(filenames) == sum(expected.values()), "imgLM.py did not produce every exposure"
    ingested = {}
    metadata = {}
    observed = Counter()
    try:
        for filename in filenames:
            header = fits.getheader(filename)
            try:
                raw = ingest_file(str(filename), store=False)
            except Exception as error:
                error.add_note(f"While ingesting simulated exposure {filename}")
                raise
            assert isinstance(raw, Raw), filename.name
            ingested[filename.name] = raw.object_id
            metadata[filename.name] = {
                "dpr_catg": header["ESO DPR CATG"],
                "dpr_tech": header["ESO DPR TECH"],
                "dpr_type": header["ESO DPR TYPE"],
                "det_dit": header["ESO DET DIT"],
                "det_ndit": header["ESO DET NDIT"],
                "drs_filter": header["ESO DRS FILTER"],
            }
            observed[(raw.dpr_catg, raw.dpr_tech, raw.dpr_type)] += 1
            assert raw.filename == filename.name
            assert raw.det_dit == pytest.approx(header["ESO DET DIT"])
            assert raw.det_ndit == header["ESO DET NDIT"]
            assert raw.drs_filter == header["ESO DRS FILTER"]
        assert observed == expected

        # Verify committed rows rather than objects retained in the object cache.
        database.disconnect()
        database.connect()
        rows = [raw for raw in Raw.select_all() if raw.filename in ingested]
        assert len(rows) == len(ingested)
        retrieved = {raw.filename: raw for raw in rows}
        assert set(retrieved) == set(ingested)
        for name, raw in retrieved.items():
            assert raw.object_id == ingested[name]
            for attribute, expected_value in metadata[name].items():
                actual_value = getattr(raw, attribute)
                if isinstance(expected_value, float):
                    assert actual_value == pytest.approx(expected_value), (name, attribute)
                else:
                    assert actual_value == expected_value, (name, attribute)
        # Re-ingestion should return the existing object rather than insert another.
        # TODO: Figure out why this is broken.
        # again = ingest_file(str(filenames[0]), store=False)
        # assert again.object_id == ingested[filenames[0].name]
    finally:
        database.rollback()
        for raw in list(Raw.select_all()):
            if raw.filename in ingested:
                context.delete(raw, commit=True)
