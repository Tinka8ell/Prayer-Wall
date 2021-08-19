# Create your views here.
import datetime, os, time

from django.http import HttpResponse, HttpResponseRedirect, JsonResponse, Http404
from django.views.decorators.csrf import csrf_exempt
from django.shortcuts import get_object_or_404, render
from django.urls import reverse
from django.views import generic
from django.db.models import F
from django.utils import timezone
from django.template import loader

#views for Wall

from .models import Prayer, Response, Prayers, PrayerForm, ResponseForm
#from .forms import PrayerForm

prayers = None
def getPrayers():
    global prayers
    if not prayers:
        prayers = Prayers()
    return prayers

def getSlotColRow(number): # extract details for this prayer
    #start = time.time()
    prayers = getPrayers()
    slot, col, row = 0, 0, 0
    try:
        slot = prayers.getSlot(int(number))
        col, row = prayers.getColRow(slot)
    except Exception as e:
        print("getSlotColRow(): exception:", e)
        prayers = None
    #print("getPanel() took", time.time() - start, "seconds")
    return slot, col, row

def getNeighbours(slot): # extract neighbours for this slot
    #start = time.time()
    prayers = getPrayers()
    previousPrayer, this, nextPrayer = 0, 0, 0
    try:
        previousPrayer, this, nextPrayer = prayers.getNumbers(slot)
    except Exception as e:
        print("getNeighbours(): exception:", e)
        prayers = None
    #print("getPanel() took", time.time() - start, "seconds")
    return previousPrayer, this, nextPrayer

def getPanel(col, row): # extract details for this panel
    #start = time.time()
    panel = "Wall/wall" + str(col) + str(row) + ".jpg"
    prayers = getPrayers()
    panelPrayers = ((-1, "", 0),) * (prayers.wrap * prayers.wrap) # add dummies
    try:
        panelPrayers = prayers.panel(int(col), int(row))
    except Exception as e:
        print("getPanel(): exception:", e)
        prayers = None
    #print("getPanel() took", time.time() - start, "seconds")
    return (panel, panelPrayers)

def index(request):
    #start = time.time()
    #print("wall: /wall")
    now = datetime.datetime.now()
    timeString = now.strftime("%Y-%m-%d %H:%M")
    prayers = getPrayers()
    wall = []
    for row in range(prayers.rows):
        for col in range(prayers.cols):
            wall.append((col, row) + getPanel(col, row))
    templateData = {
        'title' : 'Prayer Wall',
        'time': timeString,
        'wall': wall,
        'cols': prayers.cols,
        }
    #print("wall: took", time.time() - start, "seconds")
    return render(request, 'Wall/wall.html', templateData)

def panel(request, col, row):
    #start = time.time()
    print("panel: /panel/", col, "/", row)
    now = datetime.datetime.now()
    timeString = now.strftime("%Y-%m-%d %H:%M")
    panel, panelPrayers = getPanel(col, row) # extract details for this panel
    r = int(row)
    c = int(col)
    topc = str(c)
    topr = str(r - 1)
    if r <= 0:
         topc = None
         topr = None
    botc = str(c) 
    botr = str(r + 1)
    if r >= prayers.rows - 1:
         botc = None
         botr = None
    lefc = str(c - 1)
    lefr = str(r)
    if c <= 0:
          lefc = None
          lefr = None
    rigc = str(c + 1)
    rigr = str(r)
    if c >= prayers.cols - 1:
         rigc = None
         rigr = None
    templateData = {
        'title' : 'Prayer Panel ',
        'time': timeString,
        'col': col,
        'row': row,
        'upc': topc,
        'downc': botc,
        'leftc': lefc,
        'rightc': rigc,
        'upr': topr,
        'downr': botr,
        'leftr': lefr,
        'rightr': rigr,
        'panel': panel,
        'prayers': panelPrayers,
        }
    #print("panel: took", time.time() - start, "seconds")
    return render(request, 'Wall/panel.html', templateData)

def prayer(request, number):
    prayer, templateData = getPrayerData(request, number) 
    return render(request, 'Wall/prayer.html', templateData)

def getPrayerData(request, number):
    now = datetime.datetime.now()
    timeString = now.strftime("%Y-%m-%d %H:%M")
    prayer = get_object_or_404(Prayer, pk=number)
    slot, col, row = getSlotColRow(number)
    previousPrayer, this, nextPrayer = getNeighbours(slot)
    colRow = str(col) + "/" + str(row)
    paras = prayer.prayer.split("\n")
    responses = Response.objects.filter(prayer=prayer.pk)
    resps = []
    for response in responses:
        resps.append(response.response.split('\n'))
    count = int(prayer.count)
    red = 255
    if count == 0:
        red = 0
    green = 255 - count * 32
    if green < 0:
        green = 0
    colour = "rgb(" + str(red) + "," + str(green) + ",0)"
    templateData = {
        'title' : 'Details of Prayer',
        'number': number,
        'previous': previousPrayer,
        'next': nextPrayer,
        'cr': colRow,
        'col': col,
        'row': row,
        'colour': colour,
        'time': timeString,
        'subject': prayer.subject,
        'paras': paras,
        'count': prayer.count,
        'author': prayer.author,
        'responses': resps,
        }
    #print("prayer: took", time.time() - start, "seconds")
    return (prayer, templateData)

def prayed(request, number):
    prayer = get_object_or_404(Prayer, pk=number)
    prayer.count = F('count') + 1
    prayer.save()
    # Always return an HttpResponseRedirect after successfully dealing
    # with POST data. This prevents data from being posted twice if a
    # user hits the Back button.
    return HttpResponseRedirect(reverse('Wall:prayer', args=(number,)))

def newRequest(request):
    history = () # none - not (,) as ',' needed except for empty tuple
    templateData = {
        'title' : 'Request a New Prayer',
        }
    return processRequest(request, templateData, history)

def newRequested(request, number):
    templateData = {
        'title' : 'New Prayer Accepted', 
        'number': number,
        }
    return requested(request, templateData)

def prayerRequest(request, previous):
    history = (previous,) # prayer we came from
    templateData = {
        'title' : 'Request a New Prayer',
        'previous': previous,
        }
    return processRequest(request, templateData, history)

def prayerRequested(request, number, previous):
    templateData = {
        'title' : 'New Prayer Accepted',
        'number': number,
        'previous': previous,
        }
    return requested(request, templateData)

def panelRequest(request, col, row):
    history = (col, row) # none
    templateData = {
        'title' : 'Request a New Prayer',
        'col': col,
        'row': row,
        }
    return processRequest(request, templateData, history)

def panelRequested(request, number, col, row):
    templateData = {
        'title' : 'New Prayer Accepted',
        'number': number,
        'col': col,
        'row': row,
        }
    return requested(request, templateData)

def processRequest(request, templateData, history):
    now = datetime.datetime.now()
    timeString = now.strftime("%Y-%m-%d %H:%M")
    templateData['time'] = timeString
    # if this is a POST request we need to process the form data
    if request.method == 'POST':
        # create a form instance and populate it with data from the request:
        form = PrayerForm(request.POST)
        # check whether it's valid:
        if form.is_valid():
            # process the data in form.cleaned_data as required
            ### for testing
            ### templateData += {'data', form.cleaned_data}
            ### return render(request, 'Wall/index.html', templateData)
            ###
            prayer = form.save()
            # redirect to a new URL:
            return HttpResponseRedirect(reverse('Wall:prayer', args = (prayer.id,)))
        # else drop to main return as errors ...
        else:
            raise Exception("Got some errors:\n" + form.subject.errors)
    # if a GET (or any other method) we'll create a blank form
    else:
        form = PrayerForm()
    templateData['form'] = form
    # for testing: raise Exception(str(templateData))
    ### for testing
    ### return render(request, 'Wall/index.html', templateData)
    ###
    return render(request, 'Wall/request.html', templateData)
        
def requested(request, templateData):
    now = datetime.datetime.now()
    timeString = now.strftime("%Y-%m-%d %H:%M")
    templateData['time'] = timeString
    ### for testing
    ### return render(request, 'Wall/index.html', templateData)
    ###
    return render(request, 'Wall/requested.html', templateData)

def prayerRespond(request, number):
    prayer, templateData = getPrayerData(request, number) 
    templateData['title'] = 'Add response to Prayer'
    # if this is a POST request we need to process the form data
    if request.method == 'POST':
        # create a form instance and populate it with data from the request:
        form = ResponseForm(request.POST)
        # check whether it's valid:
        if form.is_valid():
            # process the data in form.cleaned_data as required
            ### for testing
            ### templateData += {'data', form.cleaned_data}
            ### return render(request, 'Wall/index.html', templateData)
            ###
            response = form.save(commit=False) # Save details, but don't commit
            response.prayer = prayer           # link the foreign key
            response.save()                    # commit save with the foreign key
            # redirect to a new URL:
            return HttpResponseRedirect(reverse('Wall:prayer', args = (number,)))
        # else drop to main return as errors ...
        else:
            raise Exception("Got some errors:\n" + form.subject.errors)
    # if a GET (or any other method) we'll create a blank form
    else:
        form = ResponseForm()
    templateData['form'] = form
    # for testing: raise Exception(str(templateData))
    ### for testing
    ### return render(request, 'Wall/index.html', templateData)
    ###
    return render(request, 'Wall/prayer.html', templateData)

def prayerResponded(request, number):
    now = datetime.datetime.now()
    timeString = now.strftime("%Y-%m-%d %H:%M")
    templateData = {
        'title' : 'Added response to prayer: ' + str(number),
        'number': number,
        'time': timeString,
        }
    ### for testing
    ### return render(request, 'Wall/index.html', templateData)
    ###
    return render(request, 'Wall/responded.html', templateData)
    
    
def json(request):
    prayers = Prayer.objects.all()
    data = {}
    for prayer in prayers:
        data[prayer.pk] = getJsonPrayer(prayer) 
    return JsonResponse(data)

def jsonPrayer(request, number):
    prayer = get_object_or_404(Prayer, pk=number)
    data = getJsonPrayer(prayer)
    return JsonResponse(data)

def getJsonPrayer(prayer):
    data = {}
    responses = getJsonResponses(prayer)
    data = {'subject': prayer.subject, 
            'prayer': prayer.prayer, 
            'author': prayer.author,
            'count': prayer.count,
            'responses': responses,
           }
    return data

def getJsonResponses(prayer):
    data = {}
    responses = Response.objects.filter(prayer=prayer)
    for response in responses:
        resp = {'subject': response.subject, 
                'response': response.response, 
                'author': response.author,
               }
        data[response.pk] = resp
    return data

@csrf_exempt
def add(request, number=None):
    if number:
        prayer, templateData = getPrayerData(request, number)
        templateData['title'] = 'Add response to Prayer'
    else:
        prayer = None
        templateData = {'title': 'Add a prayer'} 
    # Only support POST
    if request.method != 'POST':
        # raise Exception("Not POST")
        raise Http404("Page not found")
    else:
        # create a form instance and populate it with data from the request:
        if number:
            form = ResponseForm(request.POST)
            # check whether it's valid:
            if form.is_valid():
                # process the data in form.cleaned_data as required
                response = form.save(commit=False) # Save details, but don't commit
                response.prayer = prayer           # link the foreign key
                response.save()                    # commit save with the foreign key
                # redirect to a new URL:
                return HttpResponseRedirect(reverse('Wall:prayer', args = (number,)))
            # else:
            #     raise Exception("Response is invalid:")
        else:
            form = PrayerForm(request.POST)
            # check whether it's valid:
            if form.is_valid():
                # process the data in form.cleaned_data as required
                prayer = form.save()
                # redirect to a new URL:
                return HttpResponseRedirect(reverse('Wall:prayer', args = (prayer.pk,)))
            # else:
            #     raise Exception("Prayer is invalid:")
    # if we drop through then form was not valid
    # raise Exception("Dropped through")
    raise Http404("Page error")

