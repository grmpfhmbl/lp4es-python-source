Don't delete this directory. The skript "sos_exporter_gsod.py" will download the GSOD datafiles to this folder.

for i in {1995..2000}; do curl -O http://www1.ncdc.noaa.gov/pub/data/gsod/$i/111500-99999-$i.op.gz; done