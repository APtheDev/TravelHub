from rest_framework.viewsets import ModelViewSet
from rest_framework.permissions import IsAuthenticated
from rest_framework.exceptions import PermissionDenied

from .models import Trip, Destination, Activity, Participation
from .serializers import (
    TripSerializer,
    DestinationSerializer,
    ActivitySerializer,
    ParticipationSerializer
)


class TripViewSet(ModelViewSet):
    queryset = Trip.objects.all()
    serializer_class = TripSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Trip.objects.filter(
            owner=self.request.user
        )

    def perform_create(self, serializer):
        serializer.save(owner=self.request.user)


class DestinationViewSet(ModelViewSet):
    queryset = Destination.objects.all()
    serializer_class = DestinationSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Destination.objects.filter(
            trip__owner=self.request.user
        )

    def perform_create(self, serializer):
        trip = serializer.validated_data["trip"]

        if trip.owner != self.request.user:
            raise PermissionDenied(
                "Vous ne pouvez pas ajouter une destination à ce voyage."
            )

        serializer.save()

    def perform_update(self, serializer):
        trip = serializer.validated_data.get(
            "trip", serializer.instance.trip
        )

        if trip.owner != self.request.user:
            raise PermissionDenied(
                "Vous ne pouvez pas associer cette destination à ce voyage."
            )

        serializer.save()


class ActivityViewSet(ModelViewSet):
    queryset = Activity.objects.all()
    serializer_class = ActivitySerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Activity.objects.filter(
            destination__trip__owner=self.request.user
        )

    def perform_create(self, serializer):
        destination = serializer.validated_data["destination"]

        if destination.trip.owner != self.request.user:
            raise PermissionDenied(
                "Vous ne pouvez pas ajouter une activité à cette destination."
            )

        serializer.save()

    def perform_update(self, serializer):
        destination = serializer.validated_data.get(
            "destination", serializer.instance.destination
        )

        if destination.trip.owner != self.request.user:
            raise PermissionDenied(
                "Vous ne pouvez pas associer cette activité à cette destination."
            )

        serializer.save()


class ParticipationViewSet(ModelViewSet):
    queryset = Participation.objects.all()
    serializer_class = ParticipationSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Participation.objects.filter(
            trip__owner=self.request.user
        )

    def perform_create(self, serializer):
        trip = serializer.validated_data["trip"]

        if trip.owner != self.request.user:
            raise PermissionDenied(
                "Vous ne pouvez pas ajouter un participant à ce voyage."
            )

        serializer.save()

    def perform_update(self, serializer):
        trip = serializer.validated_data.get(
            "trip", serializer.instance.trip
        )

        if trip.owner != self.request.user:
            raise PermissionDenied(
                "Vous ne pouvez pas modifier cette participation."
            )

        serializer.save()