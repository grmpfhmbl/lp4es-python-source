#!/usr/bin/env python
#
# fetches the most recent METAR report for a given station from NOAA.gov and pushes it into a SOS server
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


import sys
import logging as log
import re
import traceback
import urllib.request

from metar import Metar

import utils

log.basicConfig(level=log.INFO)


if len(sys.argv) > 1:
    stationCode = str(sys.argv[1])
    if stationCode not in utils.STATIONS:
        sys.exit("Unkown station code. Must be in {}".format(utils.STATIONS.keys()))
else:
    sys.exit("Usage: python sos_exporter <station code>")


# URL where to fetch the METARs from
url = "http://weather.noaa.gov/pub/data/observations/metar/stations/{}.TXT".format(stationCode.upper())
log.info("Connecting to {}".format(url))

# fetch data
metar_html = urllib.request.urlopen(url).read().decode()

log.info("Parsing output")
# the reports fetched from NOAA have a line with the date before the METAR.
# this regex separates the two
NOAA_RE = "^(\d{4}/\d{2}/\d{2}\s+\d{2}:\d{2}.*)\n(.*)$"
matcher = re.compile(NOAA_RE, re.MULTILINE)
# we could have a document with a couple of messages, so make a list
metar_list = matcher.findall(metar_html)

log.info("Found {} METAR messages".format(len(metar_list)))
for metar in metar_list:
    log.debug("==== RAW DATA ====")
    log.debug("time: {}".format(metar[0]))
    log.debug("metar: {}".format(metar[1]))

    # use lib to parse METAR
    log.info("==== DECODED DATA ====")
    obs = Metar.Metar(metar[1])

    log.info("Original METAR: {5}\nstation: {0:4s}, time: {1:20s}, temp: {2:5s}, dew point: {3:5s}, pressure: {4:10s}, wind: {6} {7}".format(
        obs.station_id,
        obs.time.strftime("%Y-%m-%dT%H:%M:00.000+00:00"),
        obs.temp.string("C"),
        obs.dewpt.string("C"),
        obs.press.string("hpa"),
        obs.code,
        obs.wind_dir.string(),
        obs.wind_speed.string("kt")
        )
    )

    # these are the parts of the METAR we're interested in
    observations = [
        ("http://sweet.jpl.nasa.gov/2.3/propTemperature.owl#Temperature", "°C", obs.temp.value('C')),
        ("http://sweet.jpl.nasa.gov/2.3/propTemperature.owl#DewPoint", "°C", obs.dewpt.value('C')),
        ("http://sweet.jpl.nasa.gov/2.3/phenAtmoPressure.owl#Barometric", "hPa", obs.press.value('hPa')),
        ("http://sweet.jpl.nasa.gov/2.3/propSpeed.owl#WindSpeed", "kn", obs.wind_speed.value('kt')),
        ("http://vocab.example.com/phenomenon/WindDirection", "deg", obs.wind_dir.value())
    ]

    # create XML strings
    featureXml = utils.XML_FEATURE.format(obs.station_id.lower(), utils.featureId(obs.station_id), obs.station_id, utils.STATIONS[obs.station_id][1])
    timePositionXml = utils.XML_TIME_POSITION.format(obs.time.strftime("%Y-%m-%dT%H:%M:00.000+00:00"))
    procedureXref = utils.procedureXref("metar")

    # loop over all interesting observations and push them into the SOS
    for observation in observations:
        xmlObsProp = utils.XML_OBSERVED_PROPERTY.format(observation[0])
        if (observation[1] == ""):
            xmlResult = utils.XML_RESULT_TEXT.format(observation[1])
        else:
            xmlResult = utils.XML_RESULT.format(observation[1], observation[2])

        content = timePositionXml + procedureXref + xmlObsProp + featureXml + xmlResult
        insertObsXml = utils.XML_INSERT_OBS.format(utils.offeringId("metar"), content)

        log.debug(insertObsXml)

        try:
            request = urllib.request.Request(utils.POX_URL, insertObsXml.encode("UTF-8"), utils.POST_HEADER)
            resp_handle = urllib.request.urlopen(request)
            response = resp_handle.read().decode(resp_handle.headers.get_content_charset())
            log.info(response)
            resp_handle.close()
        except Exception as e:
            log.error("Error code: ", e)
            traceback.print_exc()
