# Prayers - an abstraction for the prayers
"""
Utility program to capture the json output from the PrayerWall website
and write it to file is changed since last capture.
"""


from datetime import datetime
import json
import math
from pathlib import Path
import random
import time
from urllib.error import URLError
from urllib.request import Request, urlopen


def jsonToFile(req, name):
    suffix = ("-" 
              + datetime.now().isoformat(timespec='seconds').replace(":", "-") 
              + ".json")
    # get last back up ...
    p = Path('/tmp')
    filename = p / (name + suffix)
    files = list(sorted(p.glob(name + "*")))
    ok = False
    last = {'no': 'thing'}  # so we don't match any data retreived ...
    message = 'Big Oops!'
    if len(files) > 0:
        lastfile = files[-1]
        last = json.load(lastfile.open())
    try:
        response = urlopen(req)
        ok = True
    except URLError as e:
        if hasattr(e, 'reason'):
            message = name + \
                ': We failed to reach a server.\nReason: ' + str(e.reason)
        elif hasattr(e, 'code'):
            message = (name 
                       + ': The server couldn\'t fulfill the request.\n'
                       'Error code: ' 
                       + str(e.code))
    else:
        # everything is fine
        pass
    if ok:
        # read the json from the response into the dictionary
        values = json.load(response)
        if values == last:
            message = name + ': No change, skipping backup'
        else:
            with open(filename, 'w') as f:
                json.dump(values, f)
            message = name + ': Backed up to ' + str(filename)
    return message


if __name__ == '__main__':
    print("Starting backup:", datetime.now().isoformat(timespec='seconds'))
    name = "bookings"
    req = Request("http://tinkabell.co.uk/prayerwall/booking/json/events/")
    print(jsonToFile(req, name))

    name = "prayers"
    req = Request("http://tinkabell.co.uk/prayerwall/wall/json/prayers/")
    print(jsonToFile(req, name))
