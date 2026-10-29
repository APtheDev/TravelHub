
from django.contrib.auth.models import User
from django.db import transaction
from django.http import JsonResponse

from graphene_django.views import GraphQLView

from rest_framework import status
from rest_framework.decorators import action
from rest_framework.exceptions import AuthenticationFailed, PermissionDenied
from rest_framework.generics import CreateAPIView
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet, ReadOnlyModelViewSet

from rest_framework_simplejwt.authentication import JWTAuthentication

from .models import Trip, Destination, Activity, Participation

from .serializers import (
    TripSerializer,
    DestinationSerializer,
    ActivitySerializer,
    ParticipationSerializer,
    UserSerializer,
    RegisterSerializer,
)

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


class TripViewSet(ModelViewSet):
    queryset = Trip.objects.all()
    serializer_class = TripSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Trip.objects.filter(owner=self.request.user)

    @transaction.atomic
    def perform_create(self, serializer):
        trip = serializer.save(owner=self.request.user)

        Participation.objects.get_or_create(
            user=self.request.user,
            trip=trip,
            defaults={"role": Participation.Role.ORGANIZER},
        )


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

    @action(detail=True, methods=["get"], url_path="weather")
    def get_weather(self, request, pk=None):
        destination = self.get_object()

        try:
            weather_data = get_weather_data(
                destination.city,
                destination.country
            )

            return Response(
                {
                    "destination_id": destination.id,
                    "meteo": weather_data,
                },
                status=status.HTTP_200_OK,
            )

        except DestinationNotFound as error:
            return Response(
                {"error": str(error)},
                status=status.HTTP_404_NOT_FOUND,
            )

        except MeteoNotAvailable as error:
            return Response(
                {"error": str(error)},
                status=status.HTTP_503_SERVICE_UNAVAILABLE,
            )

    @action(detail=True, methods=["get"], url_path="country")
    def get_country(self, request, pk=None):
        destination = self.get_object()

        try:
            code = get_country_code(
                destination.city,
                destination.country
            )

            country_data = get_country_data(code)

            return Response(
                {
                    "destination_id": destination.id,
                    "pays": country_data,
                },
                status=status.HTTP_200_OK,
            )

        except (DestinationNotFound, CountryNotFound) as error:
            return Response(
                {"detail": str(error)},
                status=status.HTTP_404_NOT_FOUND,
            )

        except (
            MeteoNotAvailable,
            CountriesServiceUnavailable,
        ) as error:
            return Response(
                {"detail": str(error)},
                status=status.HTTP_503_SERVICE_UNAVAILABLE,
            )

    @action(detail=True, methods=["get"], url_path="details")
    def get_details(self, request, pk=None):
        destination = self.get_object()
        destination_data = self.get_serializer(destination).data

        try:
            weather_data = get_weather_data(
                destination.city,
                destination.country
            )

            country_code = get_country_code(
                destination.city,
                destination.country
            )

            country_data = get_country_data(country_code)

            details_data = {
                "destination": destination_data,
                "meteo": weather_data,
                "pays": country_data,
            }

            return Response(
                details_data,
                status=status.HTTP_200_OK,
            )

        except (DestinationNotFound, CountryNotFound) as error:
            return Response(
                {"detail": str(error)},
                status=status.HTTP_404_NOT_FOUND,
            )

        except (
            MeteoNotAvailable,
            CountriesServiceUnavailable,
        ) as error:
            return Response(
                {"detail": str(error)},
                status=status.HTTP_503_SERVICE_UNAVAILABLE,
            )


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

        user = serializer.validated_data["user"]

        if user == trip.owner:
            raise PermissionDenied(
                "Le propriétaire est déjà organisateur du voyage."
            )

        serializer.save(role=Participation.Role.PARTICIPANT)

    def perform_update(self, serializer):
        participation = serializer.instance

        if "user" in serializer.validated_data:
            if serializer.validated_data["user"] != participation.user:
                raise PermissionDenied(
                    "Impossible de changer l'utilisateur d'une participation."
                )

        if "trip" in serializer.validated_data:
            if serializer.validated_data["trip"] != participation.trip:
                raise PermissionDenied(
                    "Impossible de changer le voyage d'une participation."
                )

        if participation.user_id == participation.trip.owner_id:
            raise PermissionDenied(
                "Impossible de modifier la participation du propriétaire."
            )

        serializer.save()

    def perform_destroy(self, instance):
        if instance.user_id == instance.trip.owner_id:
            raise PermissionDenied(
                "Impossible de retirer le propriétaire du voyage."
            )

        instance.delete()


class UserViewSet(ReadOnlyModelViewSet):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        search = self.request.query_params.get("search", "").strip()

        if len(search) < 2:
            return User.objects.none()

        return User.objects.filter(
            username__icontains=search
        ).order_by("username")[:10]


class RegisterView(CreateAPIView):
    queryset = User.objects.all()
    serializer_class = RegisterSerializer
    permission_classes = [AllowAny]
    authentication_classes = []


class JWTGraphQLView(GraphQLView):

    def dispatch(self, request, *args, **kwargs):
        if request.META.get("HTTP_AUTHORIZATION"):
            try:
                authentication = JWTAuthentication()
                result = authentication.authenticate(request)

                if result is not None:
                    request.user, request.auth = result

            except AuthenticationFailed:
                return JsonResponse(
                    {
                        "errors": [
                            {"message": "Token JWT invalide ou expiré."}
                        ]
                    },
                    status=401,
                )

        return super().dispatch(request, *args, **kwargs)
