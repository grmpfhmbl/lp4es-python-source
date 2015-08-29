# this script contains a couple of variables and functions used by
# sos_exporter and sos_graph

POX_URL = "http://130.211.71.130:8080/52n-sos-webapp/sos"

POST_HEADER = {'Content-type': 'application/xml; charset=UTF-8'}

STATIONS = {
    'LOWS': ["Salzburg Airport", "47.795 13.00388333"]
}


def procedureId(stationCode: str):
    return "http://vocab.example.com/sensorweb/procedure/metar/{}".format(stationCode.lower())


def procedureXref(stationCode: str):
    return '<om:procedure xlink:href="{}"/>'.format(procedureId(stationCode))


def offeringId(stationCode: str):
    return "http://vocab.example.com/sensorweb/offering/metar/{}".format(stationCode.lower())


def offeringXref(stationCode: str):
    return "<sos:offering>{}</sos:offering>".format(offeringId(stationCode))


def featureId(stationCode: str):
    return "http://vocab.example.com/sensorweb/feature/metar/{}".format(stationCode.lower())
