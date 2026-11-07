"""Run installed simulation block scripts and ingest their real FITS output."""

from importlib.resources import as_file, files
import os
from pathlib import Path

import pytest

from simulation_blocks import run_simulation_blocks


pytestmark = [pytest.mark.postgresql, pytest.mark.simulations]
PACKAGES = ("METIS", "ELT", "Armazones")


@pytest.fixture(scope="session")
def simulated_files(request, tmp_path_factory):
    """Execute selected scripts with their own YAML lists and output layouts."""
    try:
        resources = files("metis_simulations")
    except ModuleNotFoundError as error:
        raise pytest.UsageError("Install the simulations dependency group to run this test") from error

    blocks = request.config.getoption("--simulation-block") or ["ESO/imgLM"]
    directory = tmp_path_factory.mktemp("simulations")
    environment = os.environ.copy()
    environment.setdefault("MSIM_NCORES", "1")
    environment.setdefault("MPLBACKEND", "Agg")
    output_root = Path(environment.get("MSIM_OUTDIR", str(directory / "output"))).expanduser().resolve()
    environment["MSIM_OUTDIR"] = str(output_root)
    configured_yaml = environment.get("MSIM_YAML_DIR")
    if configured_yaml is not None:
        configured_yaml = str(Path(configured_yaml).expanduser().resolve())

    configured_irdb = request.config.getoption("--irdb-root") or environment.get("DEFAULT_IRDB_LOCATION")
    local_irdb = Path(__file__).resolve().parents[2] / "irdb"
    if configured_irdb:
        irdb = Path(configured_irdb).expanduser().resolve()
    elif all((local_irdb / package).is_dir() for package in PACKAGES):
        irdb = local_irdb
    else:
        import scopesim

        irdb = directory / "inst_pkgs"
        scopesim.download_packages(PACKAGES, save_dir=irdb)
    for relative in ("METIS/default.yaml", "ELT/ELT.yaml", "Armazones/Armazones.yaml"):
        if not (irdb / relative).is_file():
            raise pytest.UsageError(f"Missing {relative} in IRDB directory {irdb}")
    environment["DEFAULT_IRDB_LOCATION"] = str(irdb)

    with as_file(resources) as package_root:
        return run_simulation_blocks(
            package_root, blocks, output_root, directory, environment, configured_yaml,
        )


def test_simulation_files_can_be_ingested(simulated_files, metiswise_database):
    from astropy.io import fits

    # Import persistent classes only after the database fixture has initialized.
    from common.database.Context import context
    from common.database.Database import database
    from metiswise.main.dataitem import DataItem
    from metiswise.main.pro import Pro
    from metiswise.main.raw import Raw
    from metiswise.tools.ingest_file import ingest_file

    filenames = simulated_files
    assert len({path.name for path in filenames}) == len(filenames), "Blocks produced duplicate filenames"
    ingested = {}
    metadata = {}
    try:
        for filename in filenames:
            header = fits.getheader(filename)
            try:
                item = ingest_file(str(filename), store=False)
            except Exception as error:
                error.add_note(f"While ingesting simulated exposure {filename}")
                raise
            assert isinstance(item, DataItem), filename.name
            ingested[filename.name] = item.object_id
            if isinstance(item, Raw):
                expected = {
                    "dpr_catg": header["ESO DPR CATG"],
                    "dpr_tech": header["ESO DPR TECH"],
                    "dpr_type": header["ESO DPR TYPE"],
                    "det_dit": header["ESO DET DIT"],
                    "det_ndit": header["ESO DET NDIT"],
                    "drs_filter": header["ESO DRS FILTER"],
                }
            else:
                assert isinstance(item, Pro), filename.name
                expected = {"pro_catg": header["ESO PRO CATG"]}
            metadata[filename.name] = expected
            assert item.filename == filename.name

        # TODO: enable once this MR has been merged in common:
        # https://gitlab.astro-wise.org/omegacen/common/-/merge_requests/1146
        # Verify committed rows rather than objects retained in the object cache.
        # database.disconnect()
        # database.connect()
        # rows = [item for item in DataItem.select_all() if item.filename in ingested]
        # assert len(rows) == len(ingested)
        # retrieved = {item.filename: item for item in rows}
        # assert set(retrieved) == set(ingested)
        # for name, item in retrieved.items():
        #     assert item.object_id == ingested[name]
        #     for attribute, expected_value in metadata[name].items():
        #         actual_value = getattr(item, attribute)
        #         if isinstance(expected_value, float):
        #             assert actual_value == pytest.approx(expected_value), (name, attribute)
        #         else:
        #             assert actual_value == expected_value, (name, attribute)
        # Re-ingestion should return the existing object rather than insert another.
        # TODO: enable once this MR has been merged in common:
        # https://gitlab.astro-wise.org/omegacen/common/-/merge_requests/1146
        # again = ingest_file(str(filenames[0]), store=False)
        # assert again.object_id == ingested[filenames[0].name]
    finally:
        database.rollback()
        # TODO: enable once this MR has been merged in common:
        # https://gitlab.astro-wise.org/omegacen/common/-/merge_requests/1146
        # remaining = {item.filename: item for item in DataItem.select_all() if item.filename in ingested}
        # for name in reversed(ingested):
        #     context.delete(remaining[name], commit=True)
