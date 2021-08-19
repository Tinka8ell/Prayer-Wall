from django.urls import path

from . import views

app_name = 'Wall'

### add patterns for Wall

urlpatterns = [
    path('', views.index, name='index'),
]
urlpatterns = [
    path('', views.index, name='index'),                                                          # eg: /prayerwall
    path('panel/<int:col>/<int:row>/', views.panel, name='panel'),                                # eg: /prayerwall/panel/2/3
    path('prayer/<int:number>/', views.prayer, name='prayer'),                                    # eg: /prayerwall/prayer/7
    path('prayed/<int:number>/', views.prayed, name='prayed'),                                    # eg: /prayerwall/prayed/7
    path('request/', views.newRequest, name='request'),                                           # eg: /prayerwall/request/
    path('request/<int:previous>/', views.prayerRequest, name='request'),                         # eg: /prayerwall/request/7
    path('request/<int:col>/<int:row>/', views.panelRequest, name='request'),                     # eg: /prayerwall/request/2/3
    path('requested/<int:number>/', views.newRequested, name='requested'),                        # eg: /prayerwall/requested/13
    path('requested/<int:number>/<int:previous>/', views.prayerRequested, name='requested'),      # eg: /prayerwall/requested/13/7
    path('requested/<int:number>/<int:col>/<int:row>/', views.panelRequested, name='requested'),  # eg: /prayerwall/requested/13/2/3
    path('respond/<int:number>/', views.prayerRespond, name='respond'),                           # eg: /prayerwall/respond/7
    path('responded/<int:number>/', views.prayerResponded, name='responded'),                     # eg: /prayerwall/responded/7
    path('json/prayers/', views.json, name='json'),
    path('json/prayer/<int:number>/', views.jsonPrayer, name='jsonPrayer'),
    path('add/', views.add, name='add'), 
    path('add/<int:number>/', views.add, name='add'), 
]

