from django.urls import path

from . import views

app_name = 'bookings'

### add patterns for Wall

urlpatterns = [
    path('', views.index, name='index'),
    path('current/', views.current, name='current'),
    path('event/<int:number>/', views.event, name='event'),
    path('schedule/<int:schedule>/', views.schedule, name='schedule'),    
    path('booking/<int:slot>/', views.booking, name='booking'),    
    path('json/events/', views.json, name='json'),
    path('json/current/', views.jsonCurrent, name='jsonCurrent'),
    path('json/event/<int:number>/', views.jsonEvent, name='jsonEvent'),
]
