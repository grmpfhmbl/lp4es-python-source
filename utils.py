# this script contains a couple of variables and functions used by
# sos_exporter and sos_graph

POX_URL = "http://130.211.71.130:8080/52n-sos-webapp/sos"

POST_HEADER = {'Content-type': 'application/xml; charset=UTF-8'}

STATIONS = {
    'LOWS': ["Salzburg Airport", "47.795 13.00388333"],
    'LOWI': ["Innsbruck Airport", "47.260 11.344"],
    'LOWL': ["Linz Airport", "48.233 14.188"],
    'LOWW': ["Vienna Airport (Schwechat)", "48.110 16.570"],
    'LOWG': ["Graz Airport", "46.991 15.440"],
    'LOWK': ["Klagenfurt Airport", "46.650 14.333"],
}


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
