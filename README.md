MetisWISE
=========

MetisWISE is the client software for the METIS AIT archive.
It contains a Python library, called `metiswise`, to connect to the METIS AIT database and to retrieve data from the METIS AIT data server.

Installation
------------

MetisWISE uses dependencies from OmegaCEN which are in the process of being made open source.
For the moment the dependencies are only only available through a password protected pip channel.
The login credentials for that channel can be found on the [METIS AIT Archive page on the METIS wiki](https://metis.strw.leidenuniv.nl/wiki/doku.php?id=ait:archive).

First create your Python environment through your favorite means, for example using `venv`.

```bash
export OMEGACEN_CREDENTIALS=login:password
pip install \
    --extra-index-url https://ftp.eso.org/pub/dfs/pipelines/libraries \
    --extra-index-url https://ivh.github.io/pycpl/simple/ \
    --extra-index-url https://${OMEGACEN_CREDENTIALS}@pip.entropynaut.com/packages/ \
    "git+https://github.com/AstarVienna/METIS_Pipeline@main#subdirectory=metisp/pymetis" \
    metiswise
```

See the [Containerfile](Containerfile) for more instructions.

Podman
------

The easiest way to experiment with MetisWISE is through podman.
Docker should work similarly, but podman is recommended because docker is untested.
This method creates a local database instance (PostgreSQL) to experiment with.

First install podman and podman-compose through your favorite mechanism.

Then perform these workarounds (TODO: fix these)
- in `Containerfile`, replace the `OMEGACEN_CREDENTIALS` variable with the credentials from the wiki.
- in `container/compose.yml`, replace directories refering to `hugo` wit the appropriate paths.

```bash
export OMEGACEN_CREDENTIALS=username:password # See https://metis.strw.leidenuniv.nl/wiki/doku.php?id=ait:archive
podman build --secret id=OMEGACEN_CREDENTIALS,type=env -t metiswise .

cd container
podman-compose up
```

Podman compose will start four instances, that you can see with `podman ps`:
- container_postgres_1, with the test database
- container_dbviewer_1, with the web-based database viewer
- container_jupyter_1, with a jupyter notebook server
- container_metiswise_1, with bindings so X11 can be used.

podman-compose should give you a link to a Jupyter Notebook that you can open.
That is, it should print something like
```text
jupyter_1    |     To access the server, open this file in a browser:
jupyter_1    |         file:///home/metis/.local/share/jupyter/runtime/jpserver-26-open.html
jupyter_1    |     Or copy and paste one of these URLs:
jupyter_1    |         http://26c6e4169c98:8888/tree?token=0123456789abcdef
jupyter_1    |         http://127.0.0.1:8888/tree?token=0123456789abcdef
```
The last link, linking to `127.0.0.1:8888` should work, as the port is forwarded in `compose.yml`.

The dbviewer is visible at http://127.0.0.1:8080/DbView.

Setting up the database
-----------------------

The database should be setup so it has a schema.

You can connect to the metiswise container through
```bash
podman exec -ti container_metiswise_1 bash
```

Run these commands in the container.
They only have to be ran once, because the database is stored in a volume, so it persists.
```
source "${HOME}/.bashrc"
source "${HOME}/MetisWISE/toolbox/become_system_user.sh"
python "${HOME}/MetisWISE/metiswise/tools/dbtestsetup.py"
```


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

3. Upload `dist/commonwise-*.tar.gz` to https://pip.entropynaut.com/packages/metiswise/


