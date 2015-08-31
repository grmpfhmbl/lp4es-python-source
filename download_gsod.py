#!/usr/bin/env python

import datetime
import logging as log
import os
import re
import traceback
import urllib.request as request
import gzip

import utils

log.basicConfig(level=log.INFO)

YEARS = [2015, 2014]

GSOD_URL = "http://www1.ncdc.noaa.gov/pub/data/gsod/{0}/{1}"

for station in utils.STATIONS:
    for year in YEARS:
        args = utils.STATIONS[station][2:4] + [year]
        filenameIn = "{0}-{1}-{2}.op.gz".format(*args)
        filenameOut = "{0}-{1}-{2}.op".format(*args)
        filePath = "./gsod/"
        log.info("Downloading {0}".format(filenameIn))
        request.urlretrieve(GSOD_URL.format(year, filenameIn), filePath + filenameIn)
        gzFile = gzip.open(filePath + filenameIn)
        log.info("Unpacking to {0}".format(filePath + filenameOut))
        outFile = open(filePath + filenameOut, "wb")
        outFile.write(gzFile.read())
        outFile.close()
        gzFile.close()
        os.remove(filePath + filenameIn)
