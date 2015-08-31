#!/usr/bin/env python
#
# reads all files in ./gsod/ containing GSOD-Data and pushes it to
# airport codes at http://weather.rap.ucar.edu/surface/stations.txt
#
# before using this script you must setup a SOS server and create a procedure for every station
# using the example sensorml and fitting it to your needs.
#
# You need to change the POX_URL variable in utils.py to access you SOS server
#
# you also need to put all valid stations into the STATIONS-Array in utils.py
#
# Usage of this script: python sos_exporter <station code>


import datetime
import logging as log
import os
import re
import traceback
import urllib.request
import csv

import utils

log.basicConfig(level=log.INFO)

FILE_PATTERN = "^HISTALP_([A-Z]{2}_[A-Z]{3})_([A-Z]\d{2})_\d{4}_\d{4}\.csv$"

HISTALP_FILE_PATH = "./histalp/"

PHENOMENONS = {
    # last is factor for value conversion
    "R01": ["http://vocab.example.com/phenomenon/Precipitation", "mm", 1],
    "T01": ["http://vocab.example.com/phenomenon/TemperatureMean", "°C", 0.1],
    "P01": ["http://vocab.example.com/phenomenon/MeanPressure", "hPa", 0.1],
}


def filenameFilter(filename: str):
    return re.compile(FILE_PATTERN).match(filename) \
        and utils.getStationCodeFromHistalp(re.compile(FILE_PATTERN).search(filename).group(1)) != None \
        and re.compile(FILE_PATTERN).search(filename).group(2) in PHENOMENONS


def rowFilter(row):
    #check if first column of row is a year (four digits)
    return re.compile("^\d{4}$").match(row[0])


def parseRow(row, station, phenomenon):
    log.debug(row)
    for i in range(1, 13):
        if (float(row[i]) != 999999):
            dt = datetime.datetime.strptime("-".join((row[0],"{0:02d}".format(i))), "%Y-%m")
            log.debug(dt)
            xml = createXml(dt, float(row[i]) * PHENOMENONS[phenomenon][2], station, phenomenon)
            sendToSos(xml)


def createXml(dt, value, station, pheno):
    log.info("Create XML for: {0}, {1}, {2}, {3}".format(dt, value, station, pheno))
    featureXml = utils.XML_FEATURE.format(station.lower(), utils.featureId(station), station, utils.STATIONS[station][1])
    timePositionXml = utils.XML_TIME_POSITION.format(dt.strftime("%Y-%m-%dT00:00:00.000+00:00"))
    procedureXref = utils.procedureXref("histalp")

    xmlObsProp = utils.XML_OBSERVED_PROPERTY.format(PHENOMENONS[pheno][0])
    xmlResult = utils.XML_RESULT.format(PHENOMENONS[pheno][1], value)
    content = timePositionXml + procedureXref + xmlObsProp + featureXml + xmlResult
    insertObsXml = utils.XML_INSERT_OBS.format(utils.offeringId("histalp"), content)
    log.debug(insertObsXml)
    return insertObsXml


def sendToSos(xml: str):
    try:
        log.info("Inserting observation...")
        request = urllib.request.Request(utils.POX_URL, xml.encode("UTF-8"), utils.POST_HEADER)
        resp_handle = urllib.request.urlopen(request)
        response = resp_handle.read().decode(resp_handle.headers.get_content_charset())
        log.info(response)
        resp_handle.close()
    except Exception as e:
        log.error("Error code: ", e)
        traceback.print_exc()


for (dirpath, dirnames, filenames) in os.walk(HISTALP_FILE_PATH):
    for filename in filter(filenameFilter, filenames):
        log.info("Reading {}".format(filename))
        station = utils.getStationCodeFromHistalp(re.compile(FILE_PATTERN).search(filename).group(1))
        pheno = re.compile(FILE_PATTERN).search(filename).group(2)
        log.debug("Station: {0}, Phenomenon: {1}".format(station, pheno))
        with open(HISTALP_FILE_PATH + filename, newline='') as csvfile:
            fileReader = csv.reader(csvfile, delimiter=';')
            for row in filter(rowFilter, fileReader):
                parseRow(row, station, pheno)
