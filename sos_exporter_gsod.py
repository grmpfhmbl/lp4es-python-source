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
import gzip

import utils

log.basicConfig(level=log.INFO)

YEARS = [2012]

GSOD_URL = "http://www1.ncdc.noaa.gov/pub/data/gsod/{0}/{1}"

GSOD_FILE_PATH = "./gsod/"

FILE_PATTERN = "^.*\.op$"


def parseGsodLine(line: str):
    splitLine = line.split()
    log.debug("Parsing line {0}".format(splitLine))
    stationCode = utils.getStationCodeFromUsaf(splitLine[0], splitLine[1])
    date = datetime.datetime.strptime(splitLine[2], "%Y%m%d")
    if (float(splitLine[3]) != 9999.9):
        meanTemp = (float(splitLine[3]) - 32) / 1.8
    else:
        meanTemp = 9999.9

    if (float(splitLine[17].replace('*', '')) != 9999.9):
        maxTemp = (float(splitLine[17].replace('*', '')) - 32) / 1.8
    else:
        maxTemp = 9999.9

    if (float(splitLine[18].replace('*', '')) != 9999.9):
        minTemp = (float(splitLine[18].replace('*', '')) - 32) / 1.8
    else:
        minTemp = 9999.9

    if (float(splitLine[13]) != 999.9):
        meanWindSpd = float(splitLine[13])
    else:
        meanWindSpd = 999.9

    if (float(splitLine[15]) != 999.9):
        maxWindSpd = float(splitLine[15])
    else:
        maxWindSpd = 999.9

    if (float(splitLine[16]) != 999.9):
        gustWindSpd = float(splitLine[16])
    else:
        gustWindSpd = 999.9

    if (float(re.sub("[A-Z]", "", splitLine[19])) != 99.99):
        precipitation = float(re.sub("[A-Z]", "", splitLine[19])) * 25.4
    else:
        precipitation = 99.99

    log.debug(
        "Station: {0:4s}, Time: {1:20s}, Temp: {2}:{3}:{4}, mean W: {5}:{6}:{7}, precipitation: {8}".format(
            stationCode,
            date.strftime("%Y-%m-%dT23:59:59.000+00:00"),
            meanTemp,
            maxTemp,
            minTemp,
            meanWindSpd,
            maxWindSpd,
            gustWindSpd,
            precipitation,
        )
    )
    return (stationCode, date, meanTemp, maxTemp, minTemp, meanWindSpd, maxWindSpd, gustWindSpd, precipitation)


def createInsertSensorXml(obs):
    featureXml = utils.XML_FEATURE.format(obs[0].lower(), utils.featureId(obs[0]), obs[0], utils.STATIONS[obs[0]][1])
    timePositionXml = utils.XML_TIME_POSITION.format(obs[1].strftime("%Y-%m-%dT23:59:59.000+00:00"))
    procedureXref = utils.procedureXref("gsod")

    observations = [
        ("http://vocab.example.com/phenomenon/TemperatureMean", "°C"),
        ("http://vocab.example.com/phenomenon/TemperatureMax", "°C"),
        ("http://vocab.example.com/phenomenon/TemperatureMin", "°C"),
        ("http://vocab.example.com/phenomenon/WindspeedMean", "kn"),
        ("http://vocab.example.com/phenomenon/WindspeedMax", "kn"),
        ("http://vocab.example.com/phenomenon/WindspeedGust", "kn"),
        ("http://vocab.example.com/phenomenon/Precipitation", "mm"),
    ]

    result = []
    for i in range(2, len(obs)):
        if obs[i] not in [9999.9, 999.9, 99.99]:
            xmlObsProp = utils.XML_OBSERVED_PROPERTY.format(observations[i - 2][0])
            xmlResult = utils.XML_RESULT.format(observations[i - 2][1], obs[i])
            content = timePositionXml + procedureXref + xmlObsProp + featureXml + xmlResult
            insertObsXml = utils.XML_INSERT_OBS.format(utils.offeringId("gsod"), content)
            log.debug(insertObsXml)
            result.append(insertObsXml)
    return result


# download GSOD-files
for station in utils.STATIONS:
    for year in YEARS:
        args = utils.STATIONS[station][2:4] + [year]
        filenameIn = "{0}-{1}-{2}.op.gz".format(*args)
        filenameOut = "{0}-{1}-{2}.op".format(*args)
        log.info("Downloading {0}".format(filenameIn))
        urllib.request.urlretrieve(GSOD_URL.format(year, filenameIn), GSOD_FILE_PATH + filenameIn)
        gzFile = gzip.open(GSOD_FILE_PATH + filenameIn)
        log.info("Unpacking to {0}".format(GSOD_FILE_PATH + filenameOut))
        outFile = open(GSOD_FILE_PATH + filenameOut, "wb")
        outFile.write(gzFile.read())
        outFile.close()
        gzFile.close()
        os.remove(GSOD_FILE_PATH + filenameIn)


# iterate gsod directory to fetchdata
for (dirpath, dirnames, filenames) in os.walk(GSOD_FILE_PATH):
    filteredList = filter(re.compile(FILE_PATTERN).match, filenames)
    for filename in filteredList:
        fullname = os.path.join(dirpath, filename)
        log.info("Filename: {0}".format(fullname))
        f = open(fullname, 'r')
        for line in f:
            log.info("Parsing line {0}".format(line.replace("\n", "")))
            if not line.startswith("STN---"):
                parsed = parseGsodLine(line)
                log.debug(parsed)
                insertObs = createInsertSensorXml(parsed)
                log.debug(insertObs)
                for obs in insertObs:
                    try:
                        log.info("Inserting observation...")
                        request = urllib.request.Request(utils.POX_URL, obs.encode("UTF-8"), utils.POST_HEADER)
                        resp_handle = urllib.request.urlopen(request)
                        response = resp_handle.read().decode(resp_handle.headers.get_content_charset())
                        log.debug(response)
                        resp_handle.close()
                    except Exception as e:
                        log.error("Error code: ", e)
                        traceback.print_exc()
