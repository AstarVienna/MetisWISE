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

See the Dockerfile for more instructions.
