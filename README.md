MetisWISE
=========

MetisWISE is the software to run the METIS AIT archive.

Ask Hugo Buddelmeijer for the crendentials to conda.astro-wise.org.

Installation
------------

First, install conda with your favorite tools.

Then add channels
```
conda config --add channels conda-forge
conda config --add channels omegacen
conda config --add channels "https://${OMEGACEN_CONDA_CREDENTIALS}@conda.astro-wise.org/"
```

Create the metiswise environment
```
conda create -n metiswise common psycopg2 astropy pytest jupyter httpcore lxml httpx docutils pooch scipy
```
