Source for lp4es
================


prerequisites - SOS server
--------------------------

1. Install a SOS server e.g. from http://52north.org/communities/sensorweb/sos/
   Follow the installation documents from there.

2. The directory sensorml contains the needed sensor descriptions. Use the 52North
   WebClient to create all metadata.


prerequisites - python 3.4
--------------------------

We recommend using the Anaconda distribution.

1. install [Anaconda](https://store.continuum.io/cshop/anaconda/) following their instructions
2. create new environment `conda create --name lp4es python=3.4 matplotlib pandas six pip nose ipython-notebook openpyxl`
3. activate environment `source activate lp4es` (under windows omit 'source')
4. install python-metar `pip install python-metar`
   alternatively you can follow the instructions on the [python-metar GitHub-Page](https://github.com/phobson/python-metar) and install from source.

if you use a different python distribution than anaconda, you need to install matplotlib and python-metar using pip.


prerequisites data
------------------

You need to download the HISTALP data manually. Please visit http://www.zamg.ac.at/histalp/dataset/station/csv.php and
follow the instructions there. You need to put the cvs files to the _histalp_ folder.


configuration
-------------

To export data to your SOS server you'll first need to change the variable POX_URL to point to your SOS server in utils.py.
If you want to use different weather stations than the ones provided (Selection in Austria) you have change the STATIONS list.

The ICAO and USAF Codes are in [ftp://ftp.ncdc.noaa.gov/pub/data/noaa/isd-history.txt]
The code for HISTALP can be looked up at [http://www.zamg.ac.at/histalp/dataset/station/csv.php]

    POX_URL = "http://YOUR_IP:8080/52n-sos-webapp/sos"

    STATIONS = {
        # ICAOx:["Name/Descr",                 "lon lat",       "USAF",   "WBAN",  "HISTALP"]
        'LOWS': ["Salzburg Airport",           "47.795 13.004", "111500", "99999", "AT_SAL"],
        'LOWI': ["Innsbruck Airport",          "47.260 11.344", "111200", "99999", "AT_INF"],
        'LOWL': ["Linz Airport",               "48.233 14.188", "110100", "99999", "AT_HOE"],
        'LOWW': ["Vienna Airport (Schwechat)", "48.110 16.570", "110360", "99999", "AT_SWE"],
        'LOWG': ["Graz Airport",               "46.991 15.440", "112400", "99999", "AT_GFL"],
        'LOWK': ["Klagenfurt Airport",         "46.650 14.333", "112310", "99999", "AT_KLA"],
    }


METAR export
------------
The script sos_exporter_metar.py only fetches the most recent data. To build up a database it'll have to run
continuously every 30 minutes. The script needs to be called like this:

    python sos_exporter_metar.py LOWS


GSOD export
-----------
The GSOD export skript fetches the GSOD-data from [http://www1.ncdc.noaa.gov/pub/data/gsod/] for the years 2014 and 2015
for all stations configured in utils.py. The years can be configured by changing the YEARS variable in sos_exporter_gsod.py

    python sos_exporter_gsod.py

GSOD format description at [http://www1.ncdc.noaa.gov/pub/data/gsod/GSOD_DESC.txt]

HISTALP export
--------------
After you manually downloaded the HISTALP data (see above) you can start the export script

    python sos_exporter_histalp.py


Plotting data
-------------
You can plot various station data with

    python sos_graph.py STATION_NAME metar|gsod|histalp

e.g.

    python sos_graph.py LOWS gsod
