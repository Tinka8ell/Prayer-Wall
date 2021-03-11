# Prayers - an abstraction for the prayers
import time, random, math
from datetime import datetime
from urllib.request import Request, urlopen
from urllib.error import URLError
import json
from pathlib import Path

def jsonToFile(req, name):
   suffix = "-" + datetime.now().isoformat(timespec='seconds').replace(":", "-") + ".json"
   # get last back up ...
   p = Path('/tmp')
   filename = p / (name + suffix)
   files = list(sorted(p.glob(name + "*")))
   ok = False
   last = {'no': 'thing'} # so we don't match any data retreived ...
   message = 'Big Oops!'
   if len(files) > 0:
      lastfile = files[-1]
      last = json.load(lastfile.open())
   try:
      response = urlopen(req)
      ok = True
   except URLError as e:
      if hasattr(e, 'reason'):
         message = name + ': We failed to reach a server.\nReason: ' + str(e.reason)
      elif hasattr(e, 'code'):
         message = name + ': The server couldn\'t fulfill the request.\nError code: ' + str(e.code)
   else:
      # everything is fine
      pass
   if ok:
      values = json.load(response) # read the json from the response into the disctionary
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
