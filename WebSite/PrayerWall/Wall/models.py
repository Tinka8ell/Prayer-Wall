# Create your models here.

from django.db import models
from django.forms import ModelForm
from django.utils import timezone

import datetime, time

### prayer and response models

class Prayer(models.Model):
    subject = models.CharField(max_length=200)
    prayer = models.TextField(max_length=4096)
    author = models.CharField(max_length=200, blank=True, default="Anon")
    count = models.IntegerField(default=0)

    def __str__(self):
        return self.subject


class Response(models.Model):
    prayer = models.ForeignKey(Prayer, on_delete=models.CASCADE)
    subject = models.CharField(max_length=200, blank=True)
    response = models.TextField(max_length=4096)
    author = models.CharField(max_length=200, blank=True)
    
    def __str__(self):
        return self.subject


class PrayerForm(ModelForm):
    class Meta:
        model = Prayer
        fields = ['subject', 'prayer', 'author']


class ResponseForm(ModelForm):
    class Meta:
        model = Response
        fields = ['subject', 'response', 'author']


class Prayers:

    def __init__(self):
        self.listOfPrayers = {} # a dictionary of prayers, keyed of prayer number
        self.lastExtract = 0
        self.lastSummary = []
        self.rows = 3 # number of rows of panels in the screen
        self.cols = 4 # number pf columns of panels in the screen
        self.screen = self.rows * self.cols
        self.wrap = 2 # number of prayers across and down each panel
        self.wrap2 = self.wrap * self.wrap
        return

    def summary(self):
        '''
        Return a sumary list of all self.
        '''
        if time.time() - self.lastExtract > 10: # refresh every 10 seconds!
            self.listOfPrayers = Prayer.objects.all()
            self.lastExtract = time.time()
            prayers = []
            for prayer in self.listOfPrayers:
                content = [prayer.pk, prayer.subject, min(prayer.count, 9)] # limit sumary count to 9
                prayers.append(content)
            self.lastSummary = tuple(prayers)
            self.count = len(prayers)
            wrap = 2 # start from 2 x 2 prayers to a panel
            while wrap * wrap * 12 < self.count: # number on a panel * number of panels (12)
              wrap += 1
            self.wrap = wrap
            self.wrap2 = wrap * wrap
        return self.lastSummary

    def panel(self, col, row):
        '''
        Return a sumary list of all self.
        '''
        panel = []
        prayers = self.summary()
        start = (row * self.cols * self.wrap2) + (col * self.wrap)
        step = self.cols * self.wrap # length of each prayer row down screen
        stop = start + (step * self.wrap) # start of next panel below
        #print(f"start = {start}, step = {step}, stop = {stop}")
        for i in range(start, stop, step):
            line = prayers[i: i + self.wrap]
            if len(line) < self.wrap:
                line += ((0, "", 0),) * (self.wrap - len(line)) # add dummies to end of line
            panel.append(line)
        return panel

    def getSlot(self, number):
        '''
        Get the slot with this prayer
        '''
        prayers = self.summary()
        index = 0
        for item in prayers:
            if item[0] == number: # a match
                break
            index += 1
        if index >= len(prayers):
            index = 0 # if not found default to first
        return index

    def getColRow(self, index):
        '''
        Get the row and column for this slot
        '''
        #print(f"getColRow({index})")
        wholeRow = (self.cols * self.wrap) # prayers per row
        #print(f"wholeRow = {wholeRow}, self.cols = {self.cols}, self.wrap2 = {self.wrap2}")
        col = index % wholeRow # remander from prayers per row
        #print(f"col = {col}, index = {index}, wholeRow = {wholeRow}")
        row = (index - col) / wholeRow # row we are in
        #print(f"row = {row}, (index - col) = {index - col}, wholeRow = {wholeRow}")
        col = int(col / self.wrap) # actual column
        #print(f"col = {col}, index = {index}, wholeRow = {wholeRow}")
        row = int(row / self.wrap) # actual row
        #print(f"col = {col}, row = {row}")
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

    def responses(self, number):
        '''
        Return a list of responses for this prayer
        '''
        responses = []
        for pn in self.listOfPrayers.keys():
            prayer = self.listOfPrayers[pn]
            if prayer.key() == number:
                responses.append(prayer.prayer())
        return tuple(responses)

    def prayed(self, number):
        row = self.data.getRow(number)
        if row:
            self.data.incCount(row)
        return 
   
    def prayer(self, number):
        value = []
        prayer = self.listOfPrayers[number]
        if prayer:
            value = prayer.prayer()
            responses = self.responses(number)
            value.append(responses)
        return tuple(value)

