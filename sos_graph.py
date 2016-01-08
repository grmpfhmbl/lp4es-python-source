#!/usr/bin/env python
#
# This skript fetches the observations of the last 24hrs of a given station.
# Usage: python sos_exporter <station code>
#
# to access your SOS server, please change the POX_URL variable in utils
import sys
from datetime import datetime, timedelta
import logging as log
import urllib.request

import xml.etree.ElementTree as etree

#import matplotlib
#matplotlib.use('Agg')

import matplotlib.pyplot as plt
import matplotlib.ticker as ticker
import matplotlib.dates as md

import utils

log.basicConfig(level=log.INFO)

# the XML for GetObservation. For more details see <URL to a spec?>
XML_GET_OBS = """<?xml version="1.0" encoding="UTF-8"?>
<sos:GetObservation
    xmlns:sos="http://www.opengis.net/sos/2.0"
    xmlns:fes="http://www.opengis.net/fes/2.0"
    xmlns:gml="http://www.opengis.net/gml/3.2"
    xmlns:swe="http://www.opengis.net/swe/2.0"
    xmlns:xlink="http://www.w3.org/1999/xlink"
    xmlns:swes="http://www.opengis.net/swes/2.0"
    xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
    service="SOS" version="2.0.0"
    xsi:schemaLocation="http://www.opengis.net/sos/2.0 http://schemas.opengis.net/sos/2.0/sos.xsd">

    <!-- the procedure we want to query -->
    <sos:procedure>{1}</sos:procedure>

    {2}


    <sos:featureOfInterest>{0}</sos:featureOfInterest>

    <sos:responseFormat>http://www.opengis.net/om/2.0</sos:responseFormat>
</sos:GetObservation>
"""

XML_TEMP_FILTER = """
    <!-- filter for a time period -->
    <sos:temporalFilter>
        <fes:During>
            <fes:ValueReference>phenomenonTime</fes:ValueReference>
            <gml:TimePeriod gml:id="tp_1">
                <gml:beginPosition>{0}</gml:beginPosition>
                <gml:endPosition>{1}</gml:endPosition>
            </gml:TimePeriod>
        </fes:During>
    </sos:temporalFilter>
"""

if len(sys.argv) > 2:
    stationCode = str(sys.argv[1])
    if stationCode not in utils.STATIONS:
        sys.exit("Unkown station code. Must be in {}".format(utils.STATIONS.keys()))
    proc = str(sys.argv[2])
    if proc not in ['metar', 'gsod', 'histalp']:
        sys.exit("2nd argument must be either 'metar' or 'gsod' or 'histalp")
else:
    sys.exit("Usage: python sos_exporter <station code> <metar|gsod|histalp>")

try:
    if (proc == "gsod"):
        xmlTime = XML_TEMP_FILTER.format(
            (datetime.utcnow() - timedelta(days=31)).strftime("%Y-%m-%dT%H:%M:00.000+00:00"),
            datetime.utcnow().strftime("%Y-%m-%dT%H:%M:00.000+00:00")
#            "2015-07-27T10:00:00.000+00:00",
#            "2015-08-27T10:00:00.000+00:00"
        )
    elif (proc == "histalp"):
        xmlTime = "<!-- NO TEMP FILTER -->"
#        xmlTime = XML_TEMP_FILTER.format(
#            "1976-01-01T00:00:00.000+00:00",
#            "2015-08-27T00:00:00.000+00:00"
#        )
    else:
        xmlTime = XML_TEMP_FILTER.format(
            (datetime.utcnow() - timedelta(days=1)).strftime("%Y-%m-%dT%H:%M:00.000+00:00"),
            datetime.utcnow().strftime("%Y-%m-%dT%H:%M:00.000+00:00")
#            "2015-08-26T00:00:00.000+00:00",
#            "2015-08-27T00:00:00.000+00:00"
        )

    # replacing the blanks in XML_GET_OBS
    xmlRequest = XML_GET_OBS.format(
        utils.featureId(stationCode),
        utils.procedureId(proc),
        xmlTime,
    )

    log.debug(xmlRequest)

    # sending the request
    request = urllib.request.Request(
        utils.POX_URL,
        xmlRequest.encode("UTF-8"),
        utils.POST_HEADER
    )

    # getting response
    resp_handle = urllib.request.urlopen(request)
    response = resp_handle.read().decode(resp_handle.headers.get_content_charset())
    log.debug(response)
    resp_handle.close()
except Exception as e:
    log.error("Error code: ", e)
    sys.exit(1)

# response is an XML string. We parse it here.
root = etree.fromstring(response)

# namespace definitions for accessing with XPath.
# for more details see: https://docs.python.org/3/library/xml.etree.elementtree.html#parsing-xml-with-namespaces
namespaces = {
    "sos": "http://www.opengis.net/sos/2.0",
    "xsi": "http://www.w3.org/2001/XMLSchema-instance",
    "om": "http://www.opengis.net/om/2.0",
    "gml": "http://www.opengis.net/gml/3.2",
    "xlink": "http://www.w3.org/1999/xlink"
}

gmlid = "{{{0}}}id".format(namespaces["gml"])
xlinkhref = "{{{0}}}href".format(namespaces["xlink"])

# stores parsed phenomena in a dictionary with observedProperty as key
phenomenons = {}

# stores all observations with datetime as key
observations = {}

for observation in root.findall("sos:observationData/om:OM_Observation", namespaces):
    timeInstant = observation.find("om:phenomenonTime/gml:TimeInstant", namespaces)

    timestring = timeInstant.find("gml:timePosition", namespaces).text
    log.debug("New timeinstance: {0} = {1}".format(timeInstant.attrib[gmlid], timestring))
    phenomenon = observation.find("om:observedProperty", namespaces).attrib[xlinkhref]
    log.debug(phenomenon)

    if phenomenon not in phenomenons:
        phenomenons[phenomenon] = observation.find("om:result", namespaces).attrib["uom"]
        log.debug("adding phen")
        for obs in observations:
            if (len(observations[obs]) < len(list(phenomenons))):
                observations[obs].insert(list(phenomenons).index(phenomenon), 0.0)
            log.debug("====>>> {0}".format(observations[obs]))

    if timestring in observations:
        obs = observations[timestring]
    else:
        obs = [0.0] * len(list(phenomenons))

    obs[list(phenomenons).index(phenomenon)] = float(observation.find("om:result", namespaces).text)

    observations[timestring] = obs

# for graphing we need everything sorted by time.
sortedTimes = sorted(observations.keys())

# format for x and y axis text
y_formatter = ticker.ScalarFormatter(useOffset=False)
if proc == 'gsod':
    x_formatter = md.DateFormatter('%Y-%m-%d')
elif proc == 'histalp':
    x_formatter = md.DateFormatter('%Y-%m')
else:
    x_formatter = md.DateFormatter('%H:%M')

# create a number of subplots according to the number of parsed phenomena
fig, ax = plt.subplots(len(phenomenons), sharex=True, figsize=(15, 12))
fig.canvas.set_window_title("{0} data for station {1}".format(proc.upper(), stationCode))

# loop over all phenomena and print into the subplots
for num in range(0, len(phenomenons)):
    mylist = [observations[x][num] for x in sortedTimes]
    log.debug(mylist)
    ax[num].yaxis.set_major_formatter(y_formatter)
    ax[num].xaxis.set_major_formatter(x_formatter)
    ax[num].plot([datetime.strptime(i, "%Y-%m-%dT%H:%M:%S.000Z") for i in sortedTimes], mylist, 'go-')
    ax[num].set_title(list(phenomenons)[num])
    ax[num].set_ylabel(phenomenons[list(phenomenons)[num]])
    rp = ((max(mylist) - min(mylist)) / 10)
    ax[num].set_ylim(min(mylist) - rp, max(mylist) + rp)

locs, labels = plt.xticks()
plt.setp(labels, rotation=45)
plt.tight_layout()
plt.savefig("output.png")
plt.savefig("output.eps")
plt.show()
