MetisWISE
=========

MetisWISE is the client software for the METIS AIT archive.
It contains a Python library, called `metiswise`, to connect to the METIS AIT database and to retrieve data from the METIS AIT data server.

Installation
------------

MetisWISE requires Python 3.11 to 3.13, because the METIS pipeline (`pymetis`)
does not support other versions yet. Python 3.12 is used for development and CI.
Install [uv](https://docs.astral.sh/uv/getting-started/installation/), then clone
and install the project:

```bash
git clone https://github.com/AstarVienna/MetisWISE.git
cd MetisWISE
uv sync --python 3.12 --no-dev
```

uv creates a `.venv` and installs MetisWISE in editable mode. Package sources are
configured in `pyproject.toml`:

- `commonwise`, `dataserverwise`, `metis-drld`, and the METIS pipeline `pymetis`
  come from https://pip.entropynaut.com/packages/.
- `pycpl` comes from https://ivh.github.io/pycpl/simple/.
- `edps`, `pyesorex`, and `adari-core` come from
  https://ftp.eso.org/pub/dfs/pipelines/libraries.
- Other packages come from PyPI.

To include Jupyter for the example notebooks, add `--group notebook` to `uv sync`.

To install `metis-simulations` from the Entropynaut index, include the
`simulations` dependency group:

```bash
uv sync --group simulations
```

Groups can be combined, for example `uv sync --group simulations --group postgres`.
To install everything, including development tools, notebooks, simulations and
database test dependencies, use uv's built-in option:

```bash
uv sync --all-groups
```

Use `uv run --all-groups ...` when running commands with all groups enabled.

### Development installation

From the checkout, install the default `dev` dependency group (pytest, coverage
and build), optionally including notebooks:

```bash
uv sync --python 3.12 --group notebook
```

`uv sync` resolves dependencies and creates or updates `uv.lock`. Commit the
lockfile after generating it so developers and CI can share the same resolution.
Use `uv lock --upgrade` to update dependency versions intentionally. Once a
lockfile is committed, `uv sync --locked` verifies that it matches the project.

### Running tests

Run tests from the repository root:

```bash
uv run python -m pytest
```

Database tests are marked `postgresql` and skipped unless you pass
`--run-postgresql`. Install PostgreSQL with its contrib extensions (including
`pgcrypto`) and include the `postgres` dependency group:

```bash
uv sync --group postgres
uv run --group postgres python -m pytest --run-postgresql
uv run --group postgres python -m pytest --run-postgresql -m postgresql -v
uv run --group postgres python -m pytest --run-postgresql tests/test_raw.py
```

Run as a regular user, because PostgreSQL cannot initialize a cluster as root.
If PostgreSQL is outside your `PATH`, pass
`--postgresql-exec=/path/to/pg_ctl`.

The session fixture `metiswise_database` in the root `conftest.py` uses
`pytest-postgresql`'s process fixture to start a temporary local PostgreSQL
cluster on an available port. It overrides personal database configuration and
runs `metiswise.tools.dbtestsetup` in the pytest process before the first database
test.
Setup creates the persistent classes as `AWOPER`, then the harness connects as
`AWTEST` with a generated password. The server, connections and temporary files
are cleaned up even if setup or collection fails. No existing database or data
server is needed. Collection, including `--collect-only --run-postgresql`, does
not start a database.

Keep database tests in `tests/`, mark them with `pytest.mark.postgresql`, and
request `metiswise_database` as a fixture argument or with
`pytest.mark.usefixtures("metiswise_database")`. Import persistent classes inside
test functions or fixtures that depend on `metiswise_database`, so setup runs
before those imports. The initialized schema is shared across the session
because Python retains class registrations; tests should delete any objects they
commit. The initial test
commits a `Raw()` and reads it back through `Raw.select_all()` after clearing the
object cache.

The FITS provenance parsers in `metiswise.main.provenance` are independent of the
database and are tested in ordinary pytest runs.

To measure line and branch coverage using the `coverage` package included in the
test dependency group:

```bash
uv run --group postgres python -m coverage run --branch --source=metiswise -m pytest --run-postgresql
uv run --group postgres python -m coverage report --show-missing
uv run --group postgres python -m coverage html
```

Open `htmlcov/index.html` for a report with the uncovered lines highlighted.
Omit `--run-postgresql` to measure only tests that do not need a database.

The GitHub Actions workflow in `.github/workflows/tests.yml` runs on pushes to
`main` (including merges) and pull requests, and can also be started manually.
It uses Python 3.12 on Ubuntu, installs dependencies with
`uv sync --group postgres`, and runs pytest both without and with
`--run-postgresql`. CI uses the same package sources and pycpl override as local
development. JUnit XML reports are saved as
the `test-reports` workflow artifact, including when tests fail. A successful full
test run also saves coverage XML and HTML reports in that artifact. The XML can
be uploaded to a hosted coverage service such as Codecov or Coveralls.

### Simulation ingestion test

The opt-in simulation test executes installed `metis-simulations` block scripts
with the current Python interpreter, using `--small` (32×32 detector) mode. The
default is `simulationBlocks/ESO/imgLM.py`. The scripts select their own YAML
inputs and output layouts; the test does not call `metis_simulations.__main__`.

```bash
uv sync --group simulations --group postgres
uv run --no-sync python -m pytest --run-postgresql --run-simulations tests/test_simulations.py -v
```

Repeat `--simulation-block` to run an arbitrary set of installed blocks in the
specified order, then ingest their combined output in one database test:

```bash
uv run --no-sync python -m pytest --run-postgresql --run-simulations \
    --simulation-block ESO/imgLM --simulation-block ESO/imgN \
    tests/test_simulations.py -v
```

Names are relative to the package's `simulationBlocks` directory, with or without
`.py`. Each block must create or update at least one FITS file. The test discovers
those files below the output directory, ignoring untouched files from earlier
runs, so adding another block does not require hardcoded YAML lists or output
paths. It ingests raw and processed data, verifies the committed metadata after
reconnecting, and cleans up database rows. Invalid model mappings and unsupported
FITS files fail the test. `ingest_file(..., store=False)` commits metadata without
uploading files to a data server.

`MSIM_NCORES` chooses the worker count and is passed to `--nCores`; it defaults to
one. `MSIM_YAML_DIR`, `MSIM_OUTDIR`, and `MPLBACKEND` override the input directory,
output directory, and plotting backend. Relative input/output paths are resolved
from the directory where pytest is invoked. By default, each block uses the
bundled YAML directory matching its group (e.g. `YAML/ESO`), temporary output, and
the `Agg` backend. Overrides are passed through the subprocess environment and
do not change pytest's environment or working directory.

No simulator checkout is needed. The test uses a sibling `irdb` checkout if
present. Use `--irdb-root=/path/to/inst_pkgs` (or `DEFAULT_IRDB_LOCATION`) to select
instrument packages containing `METIS`, `ELT`, and `Armazones`. Otherwise ScopeSim
downloads them into the temporary directory through its Python API. Even with a
local IRDB, additional spectra, atmospheric data, or PSFs may require network
access.

Output FITS files remain in the chosen output directory for inspection. pytest
captures the scripts' output and reports a failure if any script exits with an
error; use `-s` to see progress live. Ordinary runs, including the standard CI job,
skip the simulation ingestion test unless both `--run-simulations` and
`--run-postgresql` are supplied. The small script-runner tests run without IRDB,
ScopeSim, or a database.

Podman
------

A full development environment for MetisWISE can be setup through podman
containers.  This will create a local PostgreSQL database to play with.
See the [METIS_Environmens repository(https://github.com/AstarVienna/METIS_Environments)

MetisWISE in Python
===================

Here are several examples of using the METIS Archive from Python

Storing an existing file in the archive
---------------------------------------

```python
# First import all DataItem classes.
from metiswise.main.aweimports import *

# Create a Python instance of a simulated raw exposure.
my_raw_flat = LM_FLAT_LAMP_RAW(filename="my_simulated_raw.fits")

# Store the FITS file on the data server.
my_raw_flat.store()

# Commit the metadata to the database.
my_raw_flat.commit()
```

Retrieving data from the database
---------------------------------

```python
# First import all DataItem classes.
from metiswise.main.aweimports import *

# Search for a raw flat.
all_my_raw_flats = LM_FLAT_LAMP_RAW.filename == "my_simulated_raw.fits"

# Check how many there are.
print(len(all_my_raw_flats))

# Get the first one.
my_raw_flat = all_my_raw_flats[0]

# Retrieve the FITS file from the data server
my_raw_flat.retrieve()
```

Querying using the Python prompt
--------------------------------

```python
# First import all DataItem classes.
from metiswise.main.aweimports import *

# Select all raw flats
all_my_raw_flats = LM_FLAT_LAMP_RAW.select_all()
print(len(all_my_raw_flats))

# Query flats on DIT and NDIT
my_interesting_raws = LM_FLAT_LAMP_RAW.det_ndit == 1 && LM_FLAT_LAMP_RAW.det_dit > 10
print(len(all_my_raw_flats))
```

Building and Publishing
=======================

Updating the full METIS AIT Archive goes as follows.

1. Ensure the [passwords on the wiki](https://metis.strw.leidenuniv.nl/wiki/doku.php?id=ait:archive) are still correct; update if needed.
2. [Update and publish `commonwise`.](https://gitlab.astro-wise.org/buddel/commonwise/).
2. [Update and publish `dataserverwise`.](https://gitlab.astro-wise.org/buddel/dataserverwise/).
3. Update and publish MetisWISE; see below.
4. Update the [METIS_Environments](https://github.com/AstarVienna/METIS_Environments).
5. Upgrade the production database.  TODO.
6. Upgrade the database viewer and data server software.  TODO.
7. Update the [METIS Data Reduction Server Setup](https://gitlab.strw.leidenuniv.nl/metis-ait-leiden/metis-drs-setup).

MetisWISE
---------

1. Set the version in `pyproject.toml` to the desired version.

2. Build
   ```
   uv build
   ```

3. Upload `dist/metiswise-*.tar.gz` to https://pip.entropynaut.com/packages/metiswise/
