from rest_framework.viewsets import ModelViewSet
from rest_framework.permissions import IsAuthenticated
from rest_framework.exceptions import PermissionDenied
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework import status
from .services.open_meteo import (
    get_weather_data,
    DestinationNotFound,
    MeteoNotAvailable,
    get_country_code,
)
from .services.countries import (
    get_country_data,
    CountryNotFound,
    CountriesServiceUnavailable,
)


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
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Trip.objects.filter(owner=self.request.user)

    def perform_create(self, serializer):
        serializer.save(owner=self.request.user)


class DestinationViewSet(ModelViewSet):
    queryset = Destination.objects.all()
    serializer_class = DestinationSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Destination.objects.filter(trip__owner=self.request.user)

    def perform_create(self, serializer):
        trip = serializer.validated_data["trip"]

        if trip.owner != self.request.user:
            raise PermissionDenied(
                "Vous ne pouvez pas ajouter une destination à ce voyage."
            )

        serializer.save()

    def perform_update(self, serializer):
        trip = serializer.validated_data.get("trip", serializer.instance.trip)

        if trip.owner != self.request.user:
            raise PermissionDenied(
                "Vous ne pouvez pas associer cette destination à ce voyage."
            )

        serializer.save()

    # ajout de l'action pour obtenir les données météorologiques pour une destination spécifique

    @action(detail=True, methods=["get"], url_path="weather")
    def get_weather(self, request, pk=None):

        destination = self.get_object()

        try:
            weather_data = get_weather_data(destination.city, destination.country)

            return Response(
                {"destination_id": destination.id, "meteo": weather_data},
                status=status.HTTP_200_OK,
            )

        except DestinationNotFound as error:
            return Response({"error": str(error)}, status=status.HTTP_404_NOT_FOUND)

        except MeteoNotAvailable as error:
            return Response(
                {"error": str(error)}, status=status.HTTP_503_SERVICE_UNAVAILABLE
            )

    # Ajout
    @action(detail=True, methods=["get"], url_path="country")
    def get_country(self, request, pk=None):

        destination = self.get_object()

        try:
            code = get_country_code(
                destination.city,
                destination.country
            )

            country_data = get_country_data(code)

            return Response({
                "destination_id": destination.id,
                "pays": country_data
            }, status=status.HTTP_200_OK)

        except (DestinationNotFound, CountryNotFound) as error:
            return Response(
                {"detail": str(error)},
                status=status.HTTP_404_NOT_FOUND
            )

        except (
            MeteoNotAvailable,
            CountriesServiceUnavailable
        ) as error:
            return Response(
                {"detail": str(error)},
                status=status.HTTP_503_SERVICE_UNAVAILABLE
            )


class ActivityViewSet(ModelViewSet):
    queryset = Activity.objects.all()
    serializer_class = ActivitySerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Activity.objects.filter(destination__trip__owner=self.request.user)

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
        return Participation.objects.filter(trip__owner=self.request.user)

    def perform_create(self, serializer):
        trip = serializer.validated_data["trip"]

        if trip.owner != self.request.user:
            raise PermissionDenied(
                "Vous ne pouvez pas ajouter un participant à ce voyage."
            )

        serializer.save()

    def perform_update(self, serializer):
        trip = serializer.validated_data.get("trip", serializer.instance.trip)

        if trip.owner != self.request.user:
            raise PermissionDenied("Vous ne pouvez pas modifier cette participation.")

        serializer.save()
