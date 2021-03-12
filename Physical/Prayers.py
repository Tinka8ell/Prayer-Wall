"""
Prayers - an abstraction for the prayers
"""


from datetime import datetime
import json
import math
import random
import time
from urllib.error import URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

from bs4 import BeautifulSoup


# the prefix we wanted ...
PREFIX = "http://tinkabell.co.uk/prayerwall/wall/"
# the one we have to live with ...
PREFIX = "http://tinkabell.ddns.net/prayerwall/wall/"


def prayPost(postType, number=None, postData=None):
    # postType is one of: prayed, response, prayer
    # postData is an array of 3 items ...
    address = PREFIX + postType + "/"
    if number:
        address += str(number) + "/"
    # print(f"prayPost({postType}, {number}, {postData}): '{address}'")
    if postData:
        values = {"subject": postData[0],
                  "author": postData[2],
                  }
        if number:  # then a response ...
            values["response"] = postData[1]
        else:  # then a prayer ...
            values["prayer"] = postData[1]
        # print("using values:", values)
        data = urlencode(values)
        data = data.encode('ascii')  # data should be bytes
        req = Request(address, data)  # send data for dialog
    else:
        req = Request(address)
    ok, response = submitRequest(req)
    return ok, response


def submitRequest(req):
    ok = False  # assume failed unless we succeed
    response = None
    try:
        response = urlopen(req)
        ok = True  # so far so good!
    except URLError as e:
        print(f"URLError in submitRequest('{req}')")
        if hasattr(e, 'reason'):
            print('We failed to reach a server.')
            print('Reason: ', e.reason)
        elif hasattr(e, 'code'):
            print('The server couldn\'t fulfill the request.')
            print('Error code: ', e.code)
            print(e.read())
        response = e
    else:
        # everything is fine
        pass  # the URLError.code gives the HTTP return code if required ...
    return ok, response


def getJson(address, caller):
    # print(f"{caller}: '{address}'")
    req = Request(address)
    ok, response = submitRequest(req)
    if ok:
        # read the json from the response into the disctionary
        values = json.load(response)
    else:
        raise response  # handle the error in caller
    return values


def getPrayer(number):
    address = PREFIX + "json/prayer/" + str(number) + "/"
    caller = f"getPrayer({number})"
    return getJson(address, caller)


def getAllPrayers():
    address = PREFIX + "json/prayers/"
    caller = f"getAllPrayers()"
    return getJson(address, caller)


class Prayer:

    def __init__(self, number, subject, prayer, 
                 author=None, count=0, responses=None):
        self._number = number
        self._subject = subject
        self._prayer = prayer
        self._author = author
        if author == None:
            self._author = "Anon"
        self._count = count
        self._responses = responses
        return

    def number(self):
        return self._number

    def subject(self):
        return self._subject

    def prayerText(self):
        return self._prayer

    def author(self):
        return self._author

    def count(self):
        return self._count

    def responses(self):
        responses = []
        for response in self._responses.values():
            responses.append(response.get('response'))
        return responses

    def prayer(self):
        return [
            self.number(), 
            self.subject(), 
            self.prayerText(), 
            self.author(), 
            self.count(), 
            self.responses()
            ]


class Prayers:

    def __init__(self):
        self.data = None  # place for the prayers data
        self.listOfPrayers = {}  # a dictionary of prayers, keyed of prayer number
        self.lastExtract = 0
        self.lastSummary = []
        self.rows = 3  # number of rows of panels in the screen
        self.cols = 4  # number pf columns of panels in the screen
        self.screen = self.rows * self.cols
        self.wrap = 2  # number of prayers across and down each panel
        self.wrap2 = self.wrap * self.wrap
        return

    def summary(self):
        '''
        Return a summary list of all self.
        '''
        if time.time() - self.lastExtract > 10:  # refresh every 10 seconds!
            self.load()
            self.lastExtract = time.time()
            prayers = []
            for number in self.listOfPrayers.keys():
                prayer = self.listOfPrayers[number]
                content = [number, prayer.subject(), str(
                    min(9, prayer.count()))]
                prayers.append(content)
            self.lastSummary = tuple(prayers)
            self.count = len(prayers)
            wrap = 2  # start from 2 x 2 prayers to a panel
            # number on a panel * number of panels (12)
            while wrap * wrap * 12 < self.count:
                wrap += 1
            self.wrap = wrap
            self.wrap2 = wrap * wrap
        return self.lastSummary

    def panel(self, col, row):
        '''
        Return a summary list of all self.
        '''
        panel = []
        prayers = self.summary()
        start = (row * self.cols * self.wrap2) + (col * self.wrap)
        step = self.cols * self.wrap  # length of each prayer row down screen
        stop = start + (step * self.wrap)  # start of next panel below
        #print(f"start = {start}, step = {step}, stop = {stop}")
        for i in range(start, stop, step):
            line = prayers[i: i + self.wrap]
            if len(line) < self.wrap:
                # add dummies to end of line
                line += ((0, "", 0),) * (self.wrap - len(line))
            panel.append(line)
        return panel

    def getSlot(self, number):
        '''
        Get the slot with this prayer
        '''
        prayers = self.summary()
        index = 0
        for item in prayers:
            if item[0] == number:  # a match
                break
            index += 1
        if index >= len(prayers):
            index = 0  # if not found default to first
        return index

    def getColRow(self, index):
        '''
        Get the row and column for this slot
        '''
        # print(f"getColRow({index})")
        wholeRow = (self.cols * self.wrap)  # prayers per row
        # print(f"wholeRow = {wholeRow}, self.cols = {self.cols}, "
        #       "self.wrap2 = {self.wrap2}")
        col = index % wholeRow  # remander from prayers per row
        # print(f"col = {col}, index = {index}, wholeRow = {wholeRow}")
        row = (index - col) / wholeRow  # row we are in
        # print(f"row = {row}, (index - col) = {index - col}, "
        #       "wholeRow = {wholeRow}")
        col = int(col / self.wrap)  # actual column
        # print(f"col = {col}, index = {index}, wholeRow = {wholeRow}")
        row = int(row / self.wrap)  # actual row
        # print(f"col = {col}, row = {row}")
        return col, row

    def getNumbers(self, index):
        '''
        Get the slot with this prayer
        '''
        prayers = self.summary()
        prevP = index - 1
        if prevP < 0:
            prevP = None
        else:
            prevP = prayers[prevP][0]
        nextP = index + 1
        if nextP >= len(prayers):
            nextP = None
        else:
            nextP = prayers[nextP][0]
        return (prevP, prayers[index][0], nextP)

    def prayer(self, number, force=False):
        # print(f"prayer({number}, {force})")
        item = self.listOfPrayers[int(number)]
        if force:
            try:
                data = getPrayer(int(number))
                item = self.loadPrayer(number, data)
            except Exception as e:  # any errors use existing
                # print("prayer(force) got error:", e)
                pass
        # print(f"prayer({number}), item: {item}")
        prayer = item.prayer()
        # print(f"prayer({number}), prayer: {prayer}")
        return tuple(prayer)

    def prayed(self, number):
        ok, response = prayPost("prayed", number=number)
        return ok, response

    def load(self):
        values = {}  # place for what is read in
        try:
            values = getAllPrayers()  # request all prayer data
        except:  # any errors, try and restart data once
            values = {}
            try:
                values = getAllPrayers()
            except:  # any further errors give up to next time
                values = {}
        keys = values.keys()
        if len(keys) > 0:
            # load new ones and any changes ...
            self.listOfPrayers = {}
            for key in keys:
                value = values[key]
                self.loadPrayer(key, value)
        return

    def loadPrayer(self, key, value):
        subject = value.get('subject', "No Subject")
        prayer = value.get('prayer', "No Prayer")
        author = value.get('author', "Anon")
        count = int(value.get('count', 0))
        responses = value.get('responses')
        prayer = Prayer(key, subject, prayer, author=author,
                        count=count, responses=responses)
        self.listOfPrayers[int(key)] = prayer
        return prayer


if __name__ == '__main__':
    print("Starting")
    prayers = Prayers()
    print("Loading")
    prayerDict = prayers.getAllPrayers()
    print("Prayers:", prayerDict)
    datetime.now().isoformat(timespec='minutes')
    filename = ("/tmp/" 
                + datetime.now().isoformat(timespec='seconds').replace(":", "-") 
                + ".json")
    with open(filename, 'w') as f:
        json.dump(prayerDict, f)
    '''
    prayers.Load()
    last = None
    for number in prayers.listOfPrayers:
        last = number # remember last prayer number read ...
        prayer = prayers.listOfPrayers[number]
        print(prayer.number(), prayer.subject(), "text", 
              prayer.author(), prayer.count(), prayer.responses(), 
              sep='\t')
    prayers.prayed(last) # update prayed count
    print("After update")
    for number in prayers.listOfPrayers:
        prayer = prayers.listOfPrayers[number]
        print(prayer.number(), prayer.subject(), "text", 
              prayer.author(), prayer.count(), prayer.responses(), 
              sep='\t')
    '''
