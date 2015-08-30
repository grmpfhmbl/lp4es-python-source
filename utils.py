# this script contains a couple of variables and functions used by
# sos_exporter and sos_graph

POX_URL = "http://130.211.71.130:8080/52n-sos-webapp/sos"

POST_HEADER = {'Content-type': 'application/xml; charset=UTF-8'}

STATIONS = {
    #ICAOx: ["Name/Descr",                 "lon lat",       "USAF",   "WBAN"]
    'LOWS': ["Salzburg Airport",           "47.795 13.004", "111500", "99999"],
    'LOWI': ["Innsbruck Airport",          "47.260 11.344", "111200", "99999"],
    'LOWL': ["Linz Airport",               "48.233 14.188", "110100", "99999"],
    'LOWW': ["Vienna Airport (Schwechat)", "48.110 16.570", "110360", "99999"],
    'LOWG': ["Graz Airport",               "46.991 15.440", "112400", "99999"],
    'LOWK': ["Klagenfurt Airport",         "46.650 14.333", "112310", "99999"],
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


def getStationCode(usaf: str, wban: str):
    for code in STATIONS:
        if (STATIONS[code][2] == usaf) and (STATIONS[code][3] == wban):
            return code
