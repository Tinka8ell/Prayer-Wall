from django.contrib import admin

# Register your models here.

from .models import Event, Location, Schedule, Slot, Booking

admin.site.register(Event)
admin.site.register(Location)
admin.site.register(Schedule)
admin.site.register(Slot)
admin.site.register(Booking)
