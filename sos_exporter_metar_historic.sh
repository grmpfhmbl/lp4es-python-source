#!/bin/bash
# normally this should give the directory the script is in.
# Symlinks might break it!
MYDIR=$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )

NEXT_CALL_FILE="next_call.txt"

MIN_YEAR=2005
MIN_MONTH=1

MAX_YEAR=2015
MAX_MONTH=09

STATIONS="LOWS LOWL LOWW LOWI LOWG LOWK"

if [[ -e "$NEXT_CALL_FILE" ]]; then
    params=$(cat "$NEXT_CALL_FILE")
    set -- $params
    echo "$1, $2, $3"
fi

if  ! [[ $STATIONS =~ (^| )$1($| ) ]]; then
    echo "'$1' was not in list of stations '$STATIONS'. Setting to 'LOWS'"
    STATION="LOWS"
else
    STATION=$1
fi

if [[ -z $2 ]]; then
    echo "YEAR was not set. Setting to $MIN_YEAR"
    YEAR=$MIN_YEAR
elif ! [[ $2 =~ ^[0-9]+$ ]]; then
    echo "YEAR not not numeric: '$2' --> Setting to $MIN_YEAR"
    YEAR=$MIN_YEAR
else
    YEAR=$2
fi

if [[ -z $3 ]]; then
    echo "MONTH was not set. Setting to $MIN_MONTH"
    MONTH=$MIN_MONTH
elif ! [[ $3 =~ ^[0-9]+$ ]]; then
    echo "MONTH not not numeric: '$3' --> Setting to $MIN_MIN"
    MONTH=$MIN_MONTH
else
    MONTH=$3
fi

if [[ $YEAR -lt $MIN_YEAR || \
      $MONTH -lt 1 || \
      $MONTH -gt 12 || \
      ($YEAR -eq $MIN_YEAR && $MONTH -lt $MIN_MONTH) ]]; then
    echo "$YEAR/$MONTH is not a valid date or is before min date of $MIN_YEAR/$MIN_MONTH."
    exit 1;
fi


if [[ $YEAR -gt $MAX_YEAR || \
     ($YEAR -eq $MAX_YEAR && $MONTH -gt $MAX_MONTH) ]]; then
    echo "$YEAR/$MONTH was beyond $MAX_YEAR/$MAX_MONTH. Checking if there's a next station..."
    index=0
    station_arr=($STATIONS)
    NEXT_STATION=""

    for index in ${!station_arr[@]}; do
        echo "checking if ${station_arr[$index]} -eq $STATION"
        if [[ "${station_arr[$index]}" == "$STATION" ]]; then
            index=$(($index + 1))
            NEXT_STATION=${station_arr[$index]}
            YEAR=$MIN_YEAR
            MONTH=$MIN_MONTH
            echo "next station is $NEXT_STATION - resetting date to $YEAR/$MONTH"
            break
        fi
    done
    if [[ -z $NEXT_STATION ]]; then
        echo "No next station found. Exiting."
        exit 1
    else
        STATION=$NEXT_STATION
    fi
fi

## finally run the pyhton script!
echo "Getting Data for $STATION - $YEAR/$MONTH"
echo "running python3 $MYDIR/sos_exporter_metar.py"
/usr/bin/python3 "$MYDIR/sos_exporter_metar.py" $STATION --ogimet $YEAR $MONTH

if [[ $MONTH -eq 12 ]]; then
    MONTH=1
    YEAR=$((YEAR + 1))
else
    MONTH=$(($MONTH + 1))
fi

echo "Next call will be for $STATION - $YEAR/$MONTH. Stopping at $MAX_YEAR/$MAX_MONTH"
echo "$STATION $YEAR $MONTH" > "$NEXT_CALL_FILE"
