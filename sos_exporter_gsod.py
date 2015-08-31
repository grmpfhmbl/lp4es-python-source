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

FILE_PATTERN = "^.*\.op$"

XML_INSERT_OBS = """<?xml version="1.0" encoding="UTF-8"?>
    <sos:InsertObservation
        xmlns:sos="http://www.opengis.net/sos/2.0"
        xmlns:swes="http://www.opengis.net/swes/2.0"
        xmlns:swe="http://www.opengis.net/swe/2.0"
        xmlns:sml="http://www.opengis.net/sensorML/1.0.1"
        xmlns:gml="http://www.opengis.net/gml/3.2"
        xmlns:xlink="http://www.w3.org/1999/xlink"
        xmlns:om="http://www.opengis.net/om/2.0"
        xmlns:sams="http://www.opengis.net/samplingSpatial/2.0"
        xmlns:sf="http://www.opengis.net/sampling/2.0"
        xmlns:xs="http://www.w3.org/2001/XMLSchema"
        xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
        xsi:schemaLocation="http://www.opengis.net/sos/2.0 http://schemas.opengis.net/sos/2.0/sos.xsd http://www.opengis.net/samplingSpatial/2.0 http://schemas.opengis.net/samplingSpatial/2.0/spatialSamplingFeature.xsd"
        service="SOS" version="2.0.0">
    <sos:offering>{0}</sos:offering>
    <sos:observation>
            <om:OM_Observation gml:id="o1">
            <om:type xlink:href="http://www.opengis.net/def/observationType/OGC-OM/2.0/OM_Measurement"/>
    {1}
    </om:OM_Observation>
        </sos:observation>
    </sos:InsertObservation>
"""

XML_FEATURE = """
    <om:featureOfInterest>
        <sams:SF_SpatialSamplingFeature gml:id="ssf_feature_{0}">
            <gml:identifier codeSpace="http://weather.noaa.gov/">{1}</gml:identifier>
            <gml:name>{2}</gml:name>
            <sf:type xlink:href="http://www.opengis.net/def/samplingFeatureType/OGC-OM/2.0/SF_SamplingPoint"/>
            <sf:sampledFeature xlink:href="http://sweet.jpl.nasa.gov/2.3/realm.owl#Atmosphere"/>
            <sams:shape>
                <gml:Point gml:id="feature_{0}">
                    <gml:pos srsName="http://www.opengis.net/def/crs/EPSG/0/4326">{3}</gml:pos>
                </gml:Point>
            </sams:shape>
        </sams:SF_SpatialSamplingFeature>
    </om:featureOfInterest>
"""

XML_TIME_POSITION = """
    <om:phenomenonTime>
        <gml:TimeInstant gml:id="phenomenonTime">
            <gml:timePosition>{0}</gml:timePosition>
        </gml:TimeInstant>
    </om:phenomenonTime>
    <om:resultTime xlink:href="#phenomenonTime"/>
"""

XML_OBSERVED_PROPERTY = """
    <om:observedProperty xlink:href="{0}"/>
"""

XML_RESULT = """
    <om:result xsi:type="gml:MeasureType" uom="{0}">{1}</om:result>
"""

XML_RESULT_TEXT = """
    <om:result xsi:type="xs:string">{0}</om:result>
"""


def parseGsodLine(line: str):
    splitLine = line.split()
    log.debug("Parsing line {0}".format(splitLine))
    stationCode = utils.getStationCode(splitLine[0], splitLine[1])
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
    featureXml = XML_FEATURE.format(obs[0].lower(), utils.featureId(obs[0]), obs[0], utils.STATIONS[obs[0]][1])
    timePositionXml = XML_TIME_POSITION.format(obs[1].strftime("%Y-%m-%dT23:59:59.000+00:00"))
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
            xmlObsProp = XML_OBSERVED_PROPERTY.format(observations[i - 2][0])
            xmlResult = XML_RESULT.format(observations[i - 2][1], obs[i])
            content = timePositionXml + procedureXref + xmlObsProp + featureXml + xmlResult
            insertObsXml = XML_INSERT_OBS.format(utils.offeringId("gsod"), content)
            log.debug(insertObsXml)
            result.append(insertObsXml)
    return result

YEARS = [2015, 2014]

GSOD_URL = "http://www1.ncdc.noaa.gov/pub/data/gsod/{0}/{1}"

GSOD_FILE_PATH = "./gsod/"

#download GSOD-files
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
