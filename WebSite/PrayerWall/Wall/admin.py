from django.contrib import admin

# Register your models here.

from .models import Prayer, Response

admin.site.register(Prayer)

admin.site.register(Response)

