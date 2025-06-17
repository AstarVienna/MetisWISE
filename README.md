MetisWISE
=========

MetisWISE is the client software for the METIS AIT archive.
It contains a Python library, called `metiswise`, to connect to the METIS AIT database and to retrieve data from the METIS AIT data server.

Installation
------------

MetisWISE uses dependencies from the AstroWISE conda channel.
The login credentials for that channel can be found on the [METIS AIT Archive page on the METIS wiki](https://metis.strw.leidenuniv.nl/wiki/doku.php?id=ait:archive).

First, install conda with your favorite tools.

Then add channels
```
export OMEGACEN_CONDA_CREDENTIALS=login:password # See above
conda config --add channels conda-forge
conda config --add channels omegacen
conda config --add channels "https://${OMEGACEN_CONDA_CREDENTIALS}@conda.astro-wise.org/"
```

Create the metiswise environment
```
conda create -n metiswise common psycopg2 astropy pytest jupyter httpcore lxml httpx docutils pooch scipy
```

See the Containerfile for more instructions.

Podman
------

The easiest way to experiment with MetisWISE is through podman.
Docker should work similarly, but podman is recommended because docker is untested.
This method creates a local database instance (PostgreSQL) to experiment with.

First install podman and podman-compose through your favorite mechanism.

Then perform these workarounds (TODO: fix these)
- in `Containerfile`, replace the `OMEGACEN_CONDA_CREDENTIALS` variable with the credentials from the wiki.
- in `container/compose.yml`, replace directories refering to `hugo` wit the appropriate paths.

```bash
cd container
podman build -t metiswise .
cd container
podman-compose up
```

Podman compose will start four instances, that you can see with `podman ps`:
- podman_postgres_1, with the test database
- podman_dbviewer_1, with the web-based database viewer
- podman_jupyter_1, with a jupyter notebook server
- podman_metiswise_1, with bindings so X11 can be used.

podman-compose should give you a link to a Jupyter Notebook that you can open.
That is, it should print something like
```python
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

