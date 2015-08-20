
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
