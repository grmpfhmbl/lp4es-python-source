#!/usr/bin/env python
#
# fetches data from SOS and plots it
import sys
import datetime
import logging as log
import traceback
import urllib.request

import xml.etree.ElementTree as etree

import matplotlib.pyplot as plt
import matplotlib.ticker as ticker

log.basicConfig(level=log.INFO)

XML_GET_OBS = """
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
    <sos:procedure>http://vocab.example.com/sensorweb/procedure/metar/lows</sos:procedure>
  <!--
    <sos:temporalFilter>
        <fes:During>
            <fes:ValueReference>phenomenonTime</fes:ValueReference>
            <gml:TimePeriod gml:id="tp_1">
                <gml:beginPosition>2012-11-19T14:00:00.000+01:00</gml:beginPosition>
                <gml:endPosition>2012-11-19T15:00:00.000+01:00</gml:endPosition>
            </gml:TimePeriod>
        </fes:During>
    </sos:temporalFilter>
-->
    <!-- optional -->
    <sos:responseFormat>http://www.opengis.net/om/2.0</sos:responseFormat>
</sos:GetObservation>
"""

##TODO move to utils
POST_HEADER = {'Content-type': 'application/xml; charset=UTF-8'}

POX_URL = "http://130.211.71.130:8080/52n-sos-webapp/sos"

try:
    request = urllib.request.Request(POX_URL, XML_GET_OBS.encode("UTF-8"), POST_HEADER)
    resp_handle = urllib.request.urlopen(request)
    response = resp_handle.read().decode(resp_handle.headers.get_content_charset())
    log.debug(response)
    resp_handle.close()
except Exception as e:
    log.error("Error code: ", e)
    sys.exit(1)

root = etree.fromstring(response)

namespaces = {
    "sos":   "http://www.opengis.net/sos/2.0",
    "xsi":   "http://www.w3.org/2001/XMLSchema-instance",
    "om":    "http://www.opengis.net/om/2.0",
    "gml":   "http://www.opengis.net/gml/3.2",
    "xlink": "http://www.w3.org/1999/xlink"
}
gmlid = "{{{0}}}id".format(namespaces["gml"])
xlinkhref = "{{{0}}}href".format(namespaces["xlink"])

phenomenons = {}
observations = {}

for observation in root.findall("sos:observationData/om:OM_Observation", namespaces):
    timeInstant = observation.find("om:phenomenonTime/gml:TimeInstant", namespaces)

    timestring = timeInstant.find("gml:timePosition", namespaces).text
    log.info("New timeinstance: {0} = {1}".format(timeInstant.attrib[gmlid], timestring))
    phenomenon = observation.find("om:observedProperty", namespaces).attrib[xlinkhref]
    log.info(phenomenon)

    if phenomenon not in phenomenons:
        phenomenons[phenomenon] = observation.find("om:result", namespaces).attrib["uom"]

    if timestring in observations:
        obs = observations[timestring]
    else:
        obs = []

    obs.insert(list(phenomenons).index(phenomenon), float(observation.find("om:result", namespaces).text))
    log.info(obs)

    observations[timestring] = obs

sortedTimes = sorted(observations.keys())

y_formatter = ticker.ScalarFormatter(useOffset=False)
fig, ax = plt.subplots(len(phenomenons), sharex=True)

for num in range(0, len(phenomenons)):
    mylist = [observations[x][num] for x in sortedTimes]
    log.info(mylist)
    ax[num].yaxis.set_major_formatter(y_formatter)
    ax[num].plot([datetime.datetime.strptime(i, "%Y-%m-%dT%H:%M:%S.000Z") for i in sortedTimes],
             mylist, 'bo-')
    ax[num].set_title(list(phenomenons)[num])
    ax[num].set_ylabel(phenomenons[list(phenomenons)[num]])
    rp = ((max(mylist)-min(mylist))/10)
    ax[num].set_ylim(min(mylist)-rp, max(mylist)+rp)

plt.tight_layout()
plt.show()
