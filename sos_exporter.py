#!/usr/bin/env python
#
# fetches the current report for a given station and pushes it into a SOS server
# airport codes at http://weather.rap.ucar.edu/surface/stations.txt

import sys
import datetime
import logging as log
import re
import traceback
import urllib.request

from metar import Metar

import utils

log.basicConfig(level=log.INFO)

STATIONS = {
    'LOWS': ["Salzburg Airport", "47.795 13.00388333"]
}

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

POST_HEADER = {'Content-type': 'application/xml; charset=UTF-8'}

MONTH = datetime.date.today().strftime("%m")
YEAR = datetime.date.today().strftime("%Y")
POX_URL = "http://130.211.71.130:8080/52n-sos-webapp/sos"

if len(sys.argv) > 1:
    stationCode = str(sys.argv[1])
    if stationCode not in STATIONS:
        sys.exit("Unkown station code. Must be in {}".format(STATIONS.keys()))
else:
    sys.exit("Usage: python sos_exporter <station code>")


url = "http://weather.noaa.gov/pub/data/observations/metar/stations/{}.TXT".format(stationCode.upper())
log.info("Connecting to {}".format(url))
metar_html = urllib.request.urlopen(url).read().decode()

log.info("Parsing output")
NOAA_RE = "^(\d{4}/\d{2}/\d{2}\s+\d{2}:\d{2}.*)\n(.*)$"
matcher = re.compile(NOAA_RE, re.MULTILINE)
metar_list = matcher.findall(metar_html)

log.info("Found {} METAR messages".format(len(metar_list)))
for metar in metar_list:
    log.debug("==== RAW DATA ====")
    log.debug("time: {}".format(metar[0]))
    log.debug("metar: {}".format(metar[1]))

    log.info("==== DECODED DATA ====")
    obs = Metar.Metar(metar[1])

    log.info("Original METAR: {5}\nstation: {0:4s}, time: {1:20s}, temp: {2:5s}, dew point: {3:5s}, pressure: {4:10s}".format(
        obs.station_id
        , obs.time.strftime("%Y-%m-%dT%H:%M:00.000+00:00")
        , obs.temp.string("C")
        , obs.dewpt.string("C")
        , obs.press.string("hpa")
        , obs.code))

    observations = [
        ("http://sweet.jpl.nasa.gov/2.3/propTemperature.owl#Temperature",  "°C",  obs.temp.value('C'))
        , ("http://sweet.jpl.nasa.gov/2.3/propTemperature.owl#DewPoint",    "°C",  obs.dewpt.value('C'))
        , ("http://sweet.jpl.nasa.gov/2.3/phenAtmoPressure.owl#Barometric", "hPa", obs.press.value('hPa'))
        , ("http://vocab.example.com/phenomenon/metarString", "", obs.code)
    ]

    # these are static for every observation
    featureXml = XML_FEATURE.format(obs.station_id.lower(), utils.featureId(obs.station_id), obs.station_id, STATIONS[obs.station_id][1])
    timePositionXml = XML_TIME_POSITION.format(obs.time.strftime("%Y-%m-%dT%H:%M:00.000+00:00"))
    procedureXref = utils.procedureXref(obs.station_id)

    for observation in observations:
        xmlObsProp = XML_OBSERVED_PROPERTY.format(observation[0])
        if (observation[1] == ""):
            xmlResult = XML_RESULT_TEXT.format(observation[1])
        else:
            xmlResult = XML_RESULT.format(observation[1], observation[2])

        content = timePositionXml + procedureXref + xmlObsProp + featureXml + xmlResult
        insertObsXml = XML_INSERT_OBS.format(utils.offeringId(obs.station_id), content)

        log.debug(insertObsXml)

        try:
            request = urllib.request.Request(POX_URL, insertObsXml.encode("UTF-8"), POST_HEADER)
            resp_handle = urllib.request.urlopen(request)
            response = resp_handle.read().decode(resp_handle.headers.get_content_charset())
            log.debug(response)
            resp_handle.close()
        except Exception as e:
            log.error("Error code: ", e)
            traceback.print_exc()
