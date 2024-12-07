mamba install -y common psycopg2 astropy pytest jupyter httpcore lxml httpx docutils pooch scipy

cd /repos/scopesim/ScopeSim
pip install -e .

cd /repos/scopesim/ScopeSim_Templates
pip install -e .

cd /repos/scopesim/ScopeSim_Data
pip install -e .

cd /repos/METIS_DRLD
pip install -e .



