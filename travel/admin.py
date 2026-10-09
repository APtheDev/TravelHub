from django.contrib import admin
from .models import Trip, Destination, Activity, Participation

admin.site.register(Trip)
admin.site.register(Destination)
admin.site.register(Activity)
admin.site.register(Participation)