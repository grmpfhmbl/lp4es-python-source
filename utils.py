# this script contains a couple of variables and functions used by
# sos_exporter and sos_graph

VERSION = "0.1"

POX_URL = "http://mondseewebgis.hermannklug.com/52n-sos-webapp/sos/pox"
#""http://104.155.98.248:8080/52n-sos-webapp/sos"

STATIONS = {
    # ICAOx:["Name/Descr",                 "lon lat",       "USAF",   "WBAN",  "HISTALP"]
    'LOWS': ["Salzburg Airport",           "47.795 13.004", "111500", "99999", "AT_SAL"],
#   'LOWI': ["Innsbruck Airport",          "47.260 11.344", "111200", "99999", "AT_INF"],
#   'LOWL': ["Linz Airport",               "48.233 14.188", "110100", "99999", "AT_HOE"],
#   'LOWW': ["Vienna Airport (Schwechat)", "48.110 16.570", "110360", "99999", "AT_SWE"],
#   'LOWG': ["Graz Airport",               "46.991 15.440", "112400", "99999", "AT_GFL"],
#   'LOWK': ["Klagenfurt Airport",         "46.650 14.333", "112310", "99999", "AT_KLA"],
}

POST_HEADER = {'Content-type': 'application/xml; charset=UTF-8'}

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


def procedureId(msgType: str):
    return "http://vocab.example.com/sensorweb/procedure/{0}".format(msgType.lower())


def procedureXref(msgType: str):
    return '<om:procedure xlink:href="{}"/>'.format(procedureId(msgType))


def offeringId(msgType: str):
    return "http://vocab.example.com/sensorweb/offering/{0}".format(msgType.lower())


def offeringXref(msgType: str):
    return "<sos:offering>{}</sos:offering>".format(offeringId(msgType))


def featureId(stationId: str):
    return "http://vocab.example.com/sensorweb/feature/{}".format(stationId.lower())


def getStationCodeFromUsaf(usaf: str, wban: str):
    for code in STATIONS:
        if (STATIONS[code][2] == usaf) and (STATIONS[code][3] == wban):
            return code


def getStationCodeFromHistalp(histalp: str):
    for code in STATIONS:
        if (STATIONS[code][4] == histalp):
            return code
