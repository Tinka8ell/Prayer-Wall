# Create your models here.

from django.db import models
from django.forms import ModelForm, HiddenInput
from django.utils import timezone
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _

import datetime, time

class EventManager(models.Manager):
    
    '''
    Extend an Event (id, length)
    Find the event, and the locations it uses:
    For each location (locations):
      Get schedule (event, location)
      Scan slots to find 
      For each time slot (event.length):
        Create slot (time = event start + count * hour)
    '''
    def extend_event(self, eventId, length=7):
        print(f"extend_event({eventId}, {length})")
        events = Event.objects.filter(pk=eventId)
        print("Found", len(events), "event")
        event = events[0]
        schedules = Schedule.objects.filter(event=event.pk)
        for schedule in schedules:
            scheduleId = schedule.pk
            print("Found schedule:", scheduleId)
            existingSlots = Slot.objects.filter(schedule=scheduleId)
            last = datetime.datetime(datetime.MINYEAR, 1, 1, tzinfo=timezone.utc)
            watchesUsed = []
            for slot in existingSlots:
                if slot.time > last:
                    last = slot.time
                if slot.watch not in watchesUsed:
                    watchesUsed.append(slot.watch)
            increment = datetime.timedelta(hours=1) # default to hourly
            if len(watchesUsed) > 0:
                increment = datetime.timedelta(days=1) # otherwise we are daily with watches
            for index in range(length):
                for watch in watchesUsed:
                    slot_time = last + (index + 1) * increment
                    slot = Slot(time=slot_time, schedule=schedule, watch=watch)
                    slot.save()
                    print("Created slot:", slot)
        return 

    '''
    Create an Event (name, date, length and locations)
    New Event (name, date and length)
    For each location (locations):
      If location does not exist - create
      Create schedule (event, location)
      For each time slot (event.length):
        Create slot (time = event start + count * hour)
    '''
    def create_event(self, name, start, locations, length=24):
        print(f"create_event({name}, {start}, {locations}, {length})")
        event = self.create(name=name, start_date=start, length=length)
        event.save()
        print("Created event:", event)
        start_time = event.start_date
        # do something with the event
        for place in locations:
            name = place
            size = 0
            if not isinstance(place, str): # just name, assume name and size
                name = place[0]
                if len(place) > 1:
                    size = place[1]
            location = Location.objects.create_location(name, size) # get existing location or create it
            schedule = Schedule(event=event, location=location)
            schedule.save()
            print("Created schedule:", schedule)
            for index in range(length):
                slot_time = start_time + index * datetime.timedelta(hours=1)
                slot = Slot(time=slot_time, schedule=schedule)
                slot.save()
                print("Created slot:", slot)
        return event

    '''
    Create a Watch Event (name, date, length and locations)
    New Event (name, date and length)
    For each location (locations):
      If location does not exist - create
      Create schedule (event, location)
      For each time slot (event.length):
        Create slot (time = event start + count * hour)
    '''
    def create_watch_event(self, name, start, locations, length=28):
        print(f"create_watch_event({name}, {start}, {locations}, {length})")
        event = self.create(name=name, start_date=start, length=length, isWatch=True)
        event.save()
        print("Created event:", event)
        start_time = event.start_date
        # do something with the event
        for place in locations:
            name = place
            size = 0
            if not isinstance(place, str): # just name, assume name and size
                name = place[0]
                if len(place) > 1:
                    size = place[1]
            location = Location.objects.create_location(name, size) # get existing location or create it
            schedule = Schedule(event=event, location=location)
            schedule.save()
            print("Created schedule:", schedule)
            for index in range(length):
                slot_time = start_time + index * datetime.timedelta(days=1)
                for watch in Slot.watches:
                    slot = Slot(time=slot_time, schedule=schedule, watch=watch)
                    slot.save()
                    print("Created slot:", slot)
        return event


class Event(models.Model):
    name = models.CharField(max_length=200)
    start_date = models.DateTimeField('first slot') 
    length = models.IntegerField(default=24) # number of hour slots, or day slots
    isWatch = models.BooleanField(default=False) # default is hourly

    objects = EventManager()

    def __str__(self):
        return f"{self.name} - {self.start_date} ({self.length}), id = {self.id}"


class LocationManager(models.Manager):

    def create_location(self, name, size=None):
        print(f"create_location({name}, {size})")
        location = None
        try:
            location = Location.objects.get(name=name)
            print("Found:", location)
        except Location.DoesNotExist:
            location = None
        if location:
            print("Checking size:", size, ", against location:", location.size)
            if size and size != location.size:
                location.size = size
                location.save() # update size
                print("Size changed:", location )
        else:
            location = Location(name=name, size=size)
            location.save() # new location
            print("Created location:", location)
        return location

    
class Location(models.Model):
    name = models.CharField(max_length=200)
    size  = models.IntegerField(default=24) # mumber of people per session: 0 - no limit

    objects = LocationManager()

    def __str__(self):
        return f"{self.name} ({self.size}), id = {self.id}"


class Schedule(models.Model):
    event = models.ForeignKey(Event, on_delete=models.CASCADE)
    location  = models.ForeignKey(Location, on_delete=models.CASCADE)

    def maximum(self):
        return self.location.size
        

class Slot(models.Model):
    class Part(models.IntegerChoices):
        HOURLY = 0
        MORNING = 1
        AFTERNOON = 2
        EVENING = 3
        NIGHT = 4
        ALL_DAY = 5

    allDay = (Part.ALL_DAY, )
    watches = (Part.MORNING, Part.AFTERNOON, Part.EVENING, Part.NIGHT)
    hourly = (Part.HOURLY, )

    time = models.DateTimeField('slot time') 
    schedule  = models.ForeignKey(Schedule, on_delete=models.CASCADE)
    watch = models.IntegerField(choices=Part.choices, default=Part.HOURLY)
    
    def alreadyBooked(self):
        bookings = Booking.objects.filter(slot=self.pk)
        count = 0
        for booking in bookings:
            count += booking.number
        return count
        
    def maximum(self):
        return self.schedule.maximum()
        
    def okToAdd(self, number):
        ok = True
        if self.maximum() > 0:
            ok = (self.maximum() >= (self.alreadyBooked() + number))
        return ok


class Booking(models.Model):
    person = models.CharField(max_length=200)
    slot  = models.ForeignKey(Slot, on_delete=models.CASCADE)
    number  = models.IntegerField(default=1) # number of people

    def __str__(self):
        return f"{self.person} ({self.number}), id = {self.id}"

    def maximum(self):
        return self.slot.maximum()

    def alreadyBooked(self):
        return self.slot.alreadyBooked()

    def okToAdd(self, number):
        return self.slot.okToAdd(number)

    def clean(self):
        # Don't allow adding a number that will make alreadyBooked() bigger then maximum().
        space = self.maximum() - self.alreadyBooked()
        if self.maximum() > 0 and self.number > space:
            raise( 
                ValidationError(
                    _('Too many people.  Maximum number is %(value)s'),
                    code='invalid',
                    params={'value': space},
                )
            )

class BookingForm(ModelForm):

    class Meta:
        model = Booking
        fields = ['person', 'number']

    def clean_number(self):
        number = self.cleaned_data['number']
        if number <= 0:
            raise ValidationError(
                _('Booking must be for at least 1 person'),
                code='invalid',
            )
        return number
