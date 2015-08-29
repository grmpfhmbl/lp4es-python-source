Source for lp4es
================

write something nice here :-)

prerequisites - SOS server
--------------------------

1. First you need to install a SOS server e.g. from http://52north.org/communities/sensorweb/sos/
   Follow the installation documents from there.
2. You need to create a sensor for every station you want to query. You can use the example in
   the sensorml/ directory and alter it to your needs. If you choose the 52north SOS, you
   can use their test client, to create the sensors.

prerequisites - python 3.4
--------------------------

We recommend using the Anaconda distribution.

1. install [Anaconda](https://store.continuum.io/cshop/anaconda/) following their instructions
2. create new environment `conda create --name lp4es python=3.4 matplotlib pandas six pip nose ipython-notebook openpyxl`
3. activate environment `source activate lp4es`
4. install python-metar `pip install python-metar`
   alternatively you can follow the instructions on the [python-metar GitHub-Page](https://github.com/phobson/python-metar) and install from source.

if you use a different python distribution than anaconda, you need to install matplotlib and python-metar using pip.
