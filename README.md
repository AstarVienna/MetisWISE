MetisWISE
=========

MetisWISE is the client software for the METIS AIT archive.
It contains a Python library, called `metiswise`, to connect to the METIS AIT database and to retrieve data from the METIS AIT data server.

Installation
------------

MetisWISE requires Python 3.11 to 3.13, because the METIS pipeline (`pymetis`) does not support other versions yet.
Some dependencies are not on PyPI, so pip needs three extra package indexes:
the OmegaCEN index at https://pip.entropynaut.com/packages/, the ESO pipeline libraries, and the `pycpl` index.
The OmegaCEN index hosts `commonwise`, `dataserverwise`, `metis-drld` and `pymetis`.

First create your Python environment through your favorite means, for example using `venv`.

```bash
pip install \
    --extra-index-url https://pip.entropynaut.com/packages/ \
    --extra-index-url https://ftp.eso.org/pub/dfs/pipelines/libraries \
    --extra-index-url https://ivh.github.io/pycpl/simple/ \
    metiswise
```

To also install Jupyter for the example notebooks, install `"metiswise[notebook]"` instead of `metiswise`.

### Development installation

Clone the repository and install it in editable mode, together with the `dev` dependency group (pytest, coverage and build).
Dependency groups need pip 25.1 or newer.

```bash
git clone https://github.com/AstarVienna/MetisWISE.git
cd MetisWISE
pip install \
    --extra-index-url https://pip.entropynaut.com/packages/ \
    --extra-index-url https://ftp.eso.org/pub/dfs/pipelines/libraries \
    --extra-index-url https://ivh.github.io/pycpl/simple/ \
    -e ".[notebook]" --group dev
```

### Running tests

Run tests from the repository root:

```bash
python -m pytest
```

Database tests are marked `postgresql` and skipped unless you pass
`--run-postgresql`. Install PostgreSQL with its contrib extensions (including
`pgcrypto`) and the `postgres` dependency group, using the extra package indexes
from the development installation above:

```bash
python -m pip install -e . --group postgres
python -m pytest --run-postgresql
python -m pytest --run-postgresql -m postgresql -v
python -m pytest --run-postgresql tests/test_raw.py
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

The GitHub Actions workflow in `.github/workflows/tests.yml` runs on pushes and
pull requests, and can also be started manually. It uses Python 3.12 on Ubuntu,
installs the `postgres` dependency group from the package indexes above, and runs
pytest both without and with `--run-postgresql`. It installs the required
`pycpl==1.0.4.post10` after the other dependencies to override the older pin in
`eso-pymetis`'s metadata. JUnit XML reports are saved as
the `test-reports` workflow artifact, including when tests fail.

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
   python3 -m build
   ```

3. Upload `dist/metiswise-*.tar.gz` to https://pip.entropynaut.com/packages/metiswise/
