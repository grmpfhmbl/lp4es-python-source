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

import argparse
import datetime
import logging as log
import re
import traceback
import urllib.request

from metar import Metar

import utils

SOURCES = {
    "noaa":     ["http://weather.noaa.gov/pub/data/observations/metar/stations/{}.TXT",
                 re.compile("^(\d{4}/\d{2}/\d{2}\s+\d{2}:\d{2}.*)\n(.*)$", re.MULTILINE),
                 "%Y/%m/%d %H:%M"
                 ],
    "ogimet":   ['http://www.ogimet.com/display_metars2.php?lang=en&lugar={0}&tipo=SA&ord=DIR&nil=NO&fmt=txt' +
                 '&ano={1}&mes={2}&day=01&hora=00&anof={1}&mesf={2}&dayf=31&horaf=23&minf=59&send=send',
                 re.compile("^(\d{12})\s+(METAR.*?)=$", re.MULTILINE | re.DOTALL),
                 "%Y%m%d%H%M"
                 ],
}

log.basicConfig(level=log.INFO)

parser = argparse.ArgumentParser(description="Download METAR data and push into SOS")
parser.add_argument('-v', '--version', action='version', version='%(prog)s {}'.format(utils.VERSION))

parser.add_argument('station', choices=utils.STATIONS.keys(), metavar="<ICAOCode>", help="the airport to query",
                    type=str)

parser.add_argument('year', choices=range(2005, 2016), type=int, default=datetime.date.today().strftime("%Y"),
                    nargs='?', metavar="<year>",
                    help="month to query. Ignored when querying --noaa.\nDefault: Current year (%(default)s)",
                    )

#FIXME SREI make sure month has trailing zero
parser.add_argument('month', choices=range(1, 13), type=int, default=datetime.date.today().strftime("%m"),
                    nargs='?', metavar="<month>",
                    help="month to query. Ignored when querying --noaa.\nDefault: Current month (%(default)s)",
                    )

group = parser.add_mutually_exclusive_group(required=True)
group.add_argument('--noaa', action="store_const", dest="source", const="noaa",
                   help="get most recent data from NOAA - http://weather.noaa.gov/pub/data/observations/metar/stations/")
group.add_argument('--ogimet', action="store_const", dest="source", const="ogimet",
                   help="get data from Ogimet (query limits apply) - http://www.ogimet.com/")

args = parser.parse_args()
log.debug(args)

# get all the arguments
stationCode = args.station
url = SOURCES[args.source][0].format(stationCode.upper(), args.year, args.month)
matcher = SOURCES[args.source][1]
dateFormat = SOURCES[args.source][2]

log.info("Selected station: {}".format(stationCode))
log.info("Connecting to {}".format(url))

# fetch data
metar_html = urllib.request.urlopen(url).read().decode()

log.info("Parsing output")

# reports have a timestamp in front of the METAR and
# can we can have multiple of them in the reply.
metar_list = matcher.findall(metar_html)

log.info("Found {} METAR messages".format(len(metar_list)))
for metar in metar_list:
    log.info("==== RAW DATA ====")
    log.info("time: {} - metar: {}".format(datetime.datetime.strptime(metar[0], dateFormat),
             metar[1].replace("\n", " ")))

    # parse METAR
    try:
        obs = Metar.Metar(metar[1].replace("\n", " "))

        # METAR only encodes day and time. So for historical data we have to correct the timestamp
        obs.time = datetime.datetime.strptime(metar[0], dateFormat)

        log.info("==== DECODED DATA ====\n"
                 "Original METAR: {5}\n"
                 "station: {0:4s},time: {1:20s}, temp: {2:5s}, dew point: {3:5s}, pressure: {4:10s}, wind: {6} {7}"
                 .format(obs.station_id,
                         # FIXME SREI get time from parsed time above!!
                         obs.time.strftime("%Y-%m-%dT%H:%M:00.000+00:00"),
                         obs.temp.string("C") if obs.temp else "None",
                         obs.dewpt.string("C") if obs.dewpt else "None",
                         obs.press.string("hpa") if obs.press else "None",
                         obs.code,
                         obs.wind_dir.string() if obs.wind_dir else "variable",
                         obs.wind_speed.string("kt") if obs.wind_speed else "None"
                         )
                 )

        # these are the parts of the METAR we're interested in
        observations = [
            ("http://sweet.jpl.nasa.gov/2.3/propTemperature.owl#Temperature", "°C", obs.temp.value('C') if obs.temp else None),
            ("http://sweet.jpl.nasa.gov/2.3/propTemperature.owl#DewPoint", "°C", obs.dewpt.value('C') if obs.dewpt else None),
            ("http://sweet.jpl.nasa.gov/2.3/phenAtmoPressure.owl#Barometric", "hPa", obs.press.value('hPa') if obs.press else None),
            ("http://sweet.jpl.nasa.gov/2.3/propSpeed.owl#WindSpeed", "kn", obs.wind_speed.value('kt') if obs.wind_speed else None),
            ("http://vocab.example.com/phenomenon/WindDirection", "deg", obs.wind_dir.value() if obs.wind_dir else None)
        ]

        # create XML strings
        featureXml = utils.XML_FEATURE.format(obs.station_id.lower(), utils.featureId(obs.station_id), obs.station_id,
                                              utils.STATIONS[obs.station_id][1])
        timePositionXml = utils.XML_TIME_POSITION.format(obs.time.strftime("%Y-%m-%dT%H:%M:00.000+00:00"))
        procedureXref = utils.procedureXref("metar")

        # loop over all interesting observations and push them into the SOS
        for observation in observations:
            if (observation[2]):
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
                    if "ows:Exception" not in response:
                        log.info("Observation inserted: {}".format(observation[0]))
                    elif "Observation with same values already contained in database" in response:
                        log.warn("Observation already in SOS: {}".format(observation[0]))
                    else:
                        log.info(response)
                    resp_handle.close()
                except Exception as e:
                    log.error("Error code: {}".format(e))
                    traceback.print_exc()
            else:
                log.warn("Skipped {} because of missing value".format(observation[0]))

    except Metar.ParserError as e:
        log.error("Error while parsing METAR: {0}\nMetar: {1}".format(e, metar[1].replace("\n", " ")))
