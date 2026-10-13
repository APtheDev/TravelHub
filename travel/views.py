from django.shortcuts import render

from rest_framework.viewsets import ModelViewSet

from .models import Trip, Destination, Activity, Participation
from .serializers import (
    TripSerializer,
    DestinationSerializer,
    ActivitySerializer,
    ParticipationSerializer,
)


class TripViewSet(ModelViewSet):
    queryset = Trip.objects.all()
    serializer_class = TripSerializer


class DestinationViewSet(ModelViewSet):
    queryset = Destination.objects.all()
    serializer_class = DestinationSerializer


class ActivityViewSet(ModelViewSet):
    queryset = Activity.objects.all()
    serializer_class = ActivitySerializer


class ParticipationViewSet(ModelViewSet):
    queryset = Participation.objects.all()
    serializer_class = ParticipationSerializer