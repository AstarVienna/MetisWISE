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

The database fixture also requests `metiswise_dataserver`, which starts the
installed `dataserverwise` server on a dynamically selected loopback HTTP port.
Its storage directories, SQLite file index, configuration, and logs all reside
under pytest's temporary `dataserver0` directory. It uses no external peers or
direct filesystem access from the archive client. The server is stopped when
the session ends, including after test failures. Startup errors include the
path to `process.log`; the server's own logs are in the same directory.

The archive storage client is configured for this temporary endpoint before
tests run. A FITS round-trip test uploads and commits an exposure, removes its
original local file, reconnects to PostgreSQL, and retrieves the file into a
new directory. It checks both the complete file hash and the image pixels:

```bash
uv run --no-sync python -m pytest --run-postgresql tests/test_dataserver.py -v
```

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

The opt-in simulation test executes observing blocks from
`tests/simulations/simulationBlocks`, using the installed `metis-simulations`
Python library. The YAML inputs live in `tests/simulations/YAML`; no simulator
checkout or packaged simulation resources are needed. The runner passes
`--noPsf` and uses full-size detectors.

The repository observing YAML files use point sources for IFU and LSS science
exposures.

By default, `--simulation-profile archive` prepares temporary copies of the
METIS optical YAML settings for fast archive tests:

- PSF convolution is disabled for every source, including stars and galaxies
  that the simulator's guarded `--noPsf` flag would normally leave unchanged.
- IFU sky-pixel size is doubled, reducing the internal cube's spatial area by
  about four. The detector layout, detector sizes and spectral traces are kept.

The fine wavelength sampling is retained so narrow laser lines remain available
to wavelength-calibration recipes. Detector noise, gain, linearity and FITS
header effects remain enabled. These shortcuts deliberately sacrifice optical
realism; they are intended to exercise reduction and archive infrastructure.
They do not guarantee success of every scientific recipe.

The original IRDB is untouched. Inspect the generated instrument settings in
the temporary `simulations0/archive-inputs/irdb` directory, or pass
`--simulation-profile default` to use the original IRDB settings.
Standalone block invocations use the original settings too; the archive profile
is applied by the pytest fixture.

Two single-night sets are available:

| Block | Raw exposures | Purpose |
| --- | ---: | --- |
| `functionalPipeline` (default) | 24 | The previously enabled LM-only simulations, for a functional setup test. |
| `minimalPipeline` | 78 | All entries restored, including GEO, IFU, both LSS bands and chophome, for broad data-model coverage. |

Both sets have explicit darks, flats and paired linearity exposures, share
calibrations within the night, and generate static calibration prototypes once.
Automatic `--doCalib` generation is disabled to preserve their exposure budgets.
The blocks can also run directly:

```bash
python tests/simulations/simulationBlocks/functionalPipeline.py --noPsf
```

Use `minimalPipeline.py` for the full set. Output is written below
`MSIM_OUTDIR/<block>` (`output/<block>` for standalone runs without the variable).
pytest defaults `MSIM_OUTDIR` to its temporary simulation output directory.

```bash
uv sync --group simulations --group postgres
uv run --no-sync python -m pytest --run-postgresql --run-simulations tests/test_simulations.py -v
```

Select the larger set explicitly:

```bash
uv run --no-sync python -m pytest --run-postgresql --run-simulations \
    --simulation-block minimalPipeline \
    tests/test_simulations.py -v
```

Names are relative to `tests/simulations/simulationBlocks`, with or without
`.py`. `--simulation-block` can be repeated for additional custom blocks. Run
the functional and full sets separately because they overlap and contain static
files with the same names. Each block must create or update at least one FITS
file. The test discovers
those files below the output directory, ignoring untouched files from earlier
runs, so adding another block does not require hardcoded YAML lists or output
paths. It ingests raw and processed data, uploads the FITS files to the temporary
dataserver, and downloads each into a separate directory to compare SHA-256
hashes. Invalid model mappings, unsupported FITS files, and failed transfers
fail the test. `ingest_file(..., store=False)` is available for callers
that only want to commit metadata without uploading files.

`MSIM_NCORES` chooses the worker count and is passed to `--nCores`; it defaults to
one. `MSIM_YAML_DIR`, `MSIM_OUTDIR`, and `MPLBACKEND` override the input directory,
output directory, and plotting backend. Relative input/output paths are resolved
from the directory where pytest is invoked. By default, each block uses the
local `tests/simulations/YAML` directory, temporary output, and
the `Agg` backend. Overrides are passed through the subprocess environment and
do not change pytest's environment or working directory.
`OMP_NUM_THREADS`, `OPENBLAS_NUM_THREADS` and `MKL_NUM_THREADS` default to one in
simulation subprocesses unless already set. Full-size IFU frames still need
substantial memory per worker, so increase `MSIM_NCORES` with care.

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

### Ingestion-only dataset

`tests/data/minimalPipeline.json` is a compact snapshot of 209 simulated and
processed FITS files. It was converted from a completed full run: 6.40 GB of
FITS files becomes a 4.77 MB plain JSON fixture (about 189 KB with zlib
compression, before Git's delta compression). It contains the original
filenames and HDU headers; image pixels are represented as zeros and tables
have zero rows while retaining their column definitions.
No simulation or recipe execution is required to use it.
The JSON is pretty-printed, with each header stored as a list of 80-character
physical FITS cards, including long-value `CONTINUE` cards and the `END` card.
Inspect it directly with `less tests/data/minimalPipeline.json`. Git compresses
stored objects, so the repository keeps readable JSON rather than a gzip file.
The converter still supports `.json.gz` outputs when explicitly requested.

Run its metadata-ingestion test against the temporary PostgreSQL database:

```bash
uv sync --group postgres
uv run --no-sync python -m pytest --run-postgresql \
    tests/test_ingestion_dataset.py --ingestion-dataset
```

`--ingestion-dataset=/path/to/another.json` selects a different snapshot.
This test uses `ingest_file(..., store=False)`, so it tests the data model and
provenance without uploading gigabytes of zero pixels. The separate dataserver
test covers storage/retrieval with real nonzero FITS data.

Regenerate the fixture after another complete simulation/EDPS run:

```bash
uv run --no-sync python -m metiswise.tools.ingestion_dataset create \
    /path/to/simulations0 tests/data/minimalPipeline.json --overwrite
```

The converter reads archive-classified, uncompressed FITS files recursively,
excluding linked IRDB assets. It records the source creation order (file mtimes)
so parent files can be ingested before their products. It never changes the
source files. Existing fixtures are protected unless `--overwrite` is specified;
replacements are atomic. Repeated conversions of unchanged inputs are identical.

To inspect or ingest the reconstructed files independently:

```bash
uv run --no-sync python -m metiswise.tools.ingestion_dataset restore \
    tests/data/minimalPipeline.json /tmp/metis-ingestion-fits
```

Restoration preserves HDU structure, image dimensions, pixel types, header-card
order, duplicate cards and table column definitions. Table `NAXIS2` and `PCOUNT`
are set to zero; `THEAP`, when present, is also reset to zero. No table payloads
or base64 blobs are stored. The restored files retain their large
logical sizes, but sparse zero-image regions occupy no blocks on supporting
filesystems. Nonzero FITS
scaling offsets are handled so restored pixels still have physical value zero.
The restore command refuses to overwrite files.

`CHECKSUM`/`DATASUM` cards are removed from changed image and table HDUs. Other metadata,
including ESO `DATAMD5` and recipe provenance hashes, remains the original run's
snapshot: those hashes describe the original data. These fixtures are for
ingestion, not scientific reduction or validation of the original data checksums.

### EDPS processing and ingestion

Add `--run-edps` to process the simulated files through `metis.metis_wkf` before
ingestion:

```bash
uv run --no-sync python -m pytest --run-postgresql --run-simulations --run-edps \
    tests/test_simulations.py -v
```

The selected set's explicit calibrations and static prototypes are passed to
EDPS and ingested with the science data and processing products. The default
set covers LM imaging; use `--simulation-block minimalPipeline` for the full set.

The workflow and recipes come from the installed `pymetis` package. Supply any
additional calibration data required by the workflow with `--edps-input`:

```bash
uv run --no-sync python -m pytest --run-postgresql --run-simulations --run-edps \
    --edps-input=/path/to/calibrations \
    --edps-target metis_lm_img_basic_reduce_sci tests/test_simulations.py -v
```

Repeat `--edps-input` to provide additional calibration files or directories, or
generate them using additional local `--simulation-block` options.
Repeat `--edps-target` to select tasks; omit it to use the workflow's
default targets. `--edps-timeout` sets the budget for the entire EDPS processing
phase (default 3600 seconds), separately from simulation time. On timeout the harness
saves job snapshots, cancels queued work and lets an active recipe finish before
reporting the timeout. This graceful shutdown avoids EDPS's child-process scan,
which can raise `psutil.ZombieProcess` and hide the original timeout. The budget
is therefore a soft limit; shutdown can take longer while the active recipe
finishes. Increase it for slower machines or larger runs, for example
`--edps-timeout 7200`.

The test constructs `EDPS` through its Python API with an in-memory bookkeeping
repository. It starts no HTTP server and reads no personal EDPS configuration.
Recipe execution uses the current environment's `pyesorex`, with a temporary
`PYESOREX_CONFIG` pointing to the installed METIS recipe directory. Products get
unique `PYTEST` filenames to avoid collisions in the archive. QC plot generation
is disabled for this test.

The harness uses the EDPS library rather than its CLI, so it supplies its own
live job summary. Counts and running task names appear on status changes and
at least every ten seconds, even with normal pytest output capture; `-s` is not
required. For example:

```text
EDPS [02:10] total=57 queued=41 running=1 completed=15 failed=0 missing=0; running: metis_ifu_wavecal
```

The initial message gives the recipe log directory. Individual recipe stdout
and stderr stay in per-job `esorex.stdout` and `esorex.stderr` files, rather than
being streamed to the terminal. Other test output keeps its normal pytest
capture behavior.

Incomplete associations, failed recipes, zero jobs, and zero FITS products fail
the test. The temporary `edps` directory contains `application.properties`,
`pyesorex.rc`, `submission.json`, job JSON details, and recipe stdout/stderr for
diagnosis. The archive ingests simulated inputs first, followed by the workflow's
required calibration inputs and products in dependency order.

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
