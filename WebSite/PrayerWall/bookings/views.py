# Create your views here.
import datetime, os, time, sys

from django.http import HttpResponse, HttpResponseRedirect, JsonResponse
from django.shortcuts import get_object_or_404, get_list_or_404, render
from django.urls import reverse
from django.views import generic
from django.db.models import F
from django.utils import timezone
from django.template import loader

from .models import Event, Location, Schedule, Slot, Booking, BookingForm

def index(request):
    now = datetime.datetime.now()
    timeString = now.strftime("%Y-%m-%d %H:%M")
    events = get_list_or_404(Event)
    count = len(events)
    data = []
    for event in events:
        start = event.start_date.strftime("%A, %d %b %Y from %H:%M")
        data.append({'name': event.name, 
                     'start': start,
                     'number': event.pk,
                    }) 
    templateData = {
        'title' : 'All events',
        'count': count,
        'events': data,
        'size': len(data),
        'time': timeString,
        }
    return render(request, 'bookings/events.html', templateData)

def current(request):
    # redirect to the event page for the latest event
    now = datetime.datetime.now()
    timeString = now.strftime("%Y-%m-%d %H:%M")
    events = get_list_or_404(Event)
    latest = events[-1]
    number = latest.pk
    return HttpResponseRedirect(reverse('bookings:event', args = (number,)))

def event(request, number):
    now = datetime.datetime.now()
    timeString = now.strftime("%Y-%m-%d %H:%M")
    event = get_object_or_404(Event, pk=number)
    isWatch = event.isWatch
    start = event.start_date.strftime("%A, %d %b %Y from %H:%M")
    print(f"Event: {number}, start: {start}, isWatch = {isWatch}", file=sys.stderr)
    schedules = Schedule.objects.filter(event=event.pk)
    data = []
    for schedule in schedules:
        location = Location.objects.get(pk=schedule.location.pk)
        loc = {'name': location.name, 
               'size': location.size,
               'schedule': schedule.pk,
              }
        data.append(loc)
    templateData = {
        'title' : event.name,
        'start': start,
        'number': event.pk,
        'length': event.length,
        'locations': data,
        'time': timeString,
        }
    print(f"Event: {number}, start: {start}, isWatch = {isWatch}, about to render", file=sys.stderr)
    return render(request, 'bookings/locations.html', templateData)

def schedule(request, schedule):
    now = datetime.datetime.now()
    timeString = now.strftime("%Y-%m-%d %H:%M")
    schedule_object = get_object_or_404(Schedule, pk=schedule)
    event = schedule_object.event
    number = event.pk
    print(f"Schedule: {schedule}", file=sys.stderr)
    isWatch = event.isWatch
    start = event.start_date.strftime("%A, %d %b %Y from %H:%M")
    if isWatch:
        start = event.start_date.strftime("%A, %d %b %Y")
    print(f"Schedule: {schedule}, start: {start}, isWatch = {isWatch}", file=sys.stderr)
    # get alternative venues
    alternatives = Schedule.objects.filter(event=event.pk).exclude(pk=schedule)
    alt = []
    for alternate in alternatives:
        alt.append((alternate.id, alternate.location.name))
    location = schedule_object.location
    bookings = {}
    loc = {'name': location.name, 
           'size': location.size,
           'schedule': schedule,
          }
    slots = Slot.objects.filter(schedule=schedule).order_by('time', 'watch')
    loc['count'] = len(slots)
    for slot in slots:
        people = []
        time = slot.time.strftime("%a %H:%M")
        if slot.watch != Slot.Part.HOURLY:
            time = slot.time.strftime("%a %d %b: ") + Slot.Part(slot.watch).label
        booked = Booking.objects.filter(slot=slot.pk)
        count = 0
        for booking in booked:
            count += booking.number
            people.append(booking.person)
        if count == 0:
            status = 'slotFree' # colour if available
        else:
            if location.size > 0 and count >= location.size: # so full
                status = 'slotFull' # colour if not available
            else:
                status = 'slotCovered' # colour if covered
        bookings[time] = { 'people': people,
                           'count': count,
                           'status': status,
                           'slot': slot.pk,
                           'watch': slot.watch,
                         }
    loc['bookings'] = bookings
    templateData = {
        'title' : event.name,
        'start': start,
        'number': event.pk,
        'length': event.length,
        'time': timeString,
        'location': loc,
        'alternatives': alt,
        'isWatch': isWatch,
        }
    print(f"Schedule: {schedule}, start: {start}, isWatch = {isWatch}, about to render", file=sys.stderr)
    return render(request, 'bookings/bookings.html', templateData)

def booking(request, slot):
    now = datetime.datetime.now()
    timeString = now.strftime("%Y-%m-%d %H:%M")
    # need to detct what sort of slot!
    slot_object = get_object_or_404(Slot, pk=slot)
    schedule = slot_object.schedule
    event = schedule.event
    isWatch = event.isWatch
    start = event.start_date.strftime("%A, %d %b %Y from %H:%M")
    if isWatch:
        start = event.start_date.strftime("%A, %d %b %Y")
    location = schedule.location
    time = slot_object.time.strftime("%a %H:%M")
    if slot_object.watch != Slot.Part.HOURLY:
        time = slot_object.time.strftime("%a %d %b: ") + Slot.Part(slot_object.watch).label
    templateData = {
        'title' : event.name,
        'location': location.name,
        'slot': time,
        'number': slot,
        'time': timeString,
        'isWatch': isWatch,
        'watch': slot_object.watch,
        }
    # if this is a POST request we need to process the form data
    if request.method == 'POST':
        # create a form instance and populate it with data from the request:
        booking = Booking(slot=slot_object)
        form = BookingForm(request.POST, instance=booking)
        # check whether it's valid:
        if form.is_valid():
            # process the data in form.cleaned_data as required
            booking.save()                    # commit save with the foreign key
            # redirect to a new URL:
            return HttpResponseRedirect(reverse('bookings:schedule', args = (schedule.pk,)))
        # else drop to main return as errors ...
    # if a GET (or any other method) we'll create a blank form
    else:
        form = BookingForm()
    templateData['form'] = form
    return render(request, 'bookings/booking.html', templateData)
    
    
def json(request):
    now = datetime.datetime.now()
    timeString = now.strftime("%Y-%m-%d %H:%M")
    events = get_list_or_404(Event)
    data = {}
    for event in events:
        start = event.start_date.strftime("%A, %d %b %Y from %H:%M")
        number = event.pk
        schedules = getJson(number)
        data[number] = {'name': event.name, 
                         'start': start,
                         'length': event.length,
                         'schedules': schedules,
                        }
    return JsonResponse(data)

def jsonCurrent(request):
    # redirect to the event page for the latest event
    now = datetime.datetime.now()
    timeString = now.strftime("%Y-%m-%d %H:%M")
    events = get_list_or_404(Event)
    latest = events[-1]
    return returnJsonEvent(request, latest)

def jsonEvent(request, number):
    now = datetime.datetime.now()
    timeString = now.strftime("%Y-%m-%d %H:%M")
    event = get_object_or_404(Event, pk=number)
    return returnJsonEvent(request, event)

def returnJsonEvent(request, event):
    number = event.pk
    start = event.start_date.strftime("%A, %d %b %Y from %H:%M")
    schedules = getJson(number)
    data = {'name': event.name, 
            'start': start,
            'schedules': schedules,
           }
    return JsonResponse(data)

def getJson(number):
    data = {}
    schedules = Schedule.objects.filter(event=number)
    for schedule in schedules:
        location = Location.objects.get(pk=schedule.location.pk)
        sched = schedule.pk
        slots = getSlots(sched)
        loc = {'name': location.name, 
               'size': location.size,
               'slots': slots,
              }
        data[sched] = loc
    return data

def getSlots(number):
    data = {}
    slots = Slot.objects.filter(schedule=number).order_by('time')
    for slot in slots:
        people = []
        time = slot.time.strftime("%a %H:%M")
        bookings = Booking.objects.filter(slot=slot.pk)
        for booking in bookings:
            people.append({'person': booking.person,
                           'number': booking.number,
                          })
        data[time] = {'people': people, }
    return data

