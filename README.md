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
