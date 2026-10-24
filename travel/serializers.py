from rest_framework import serializers
from .models import Trip, Destination, Activity, Participation


class TripSerializer(serializers.ModelSerializer):
    class Meta:
        model = Trip
        fields = "__all__"
        read_only_fields = ["owner"]

    def validate(self, data):
        start_date = data["start_date"]
        end_date = data["end_date"]

        if start_date > end_date:
            raise serializers.ValidationError(
                "La date de début doit être avant la date de fin."
            )

        return data


class DestinationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Destination
        fields = "__all__"

    def validate(self, data):
        trip = data["trip"]
        arrival_date = data["arrival_date"]
        departure_date = data["departure_date"]

        if arrival_date > departure_date:
            raise serializers.ValidationError(
                "La date d'arrivée doit être avant la date de départ."
            )

        if arrival_date < trip.start_date:
            raise serializers.ValidationError(
                "La destination ne peut pas commencer avant le voyage."
            )

        if departure_date > trip.end_date:
            raise serializers.ValidationError(
                "La destination ne peut pas terminer après le voyage."
            )

        return data


class ActivitySerializer(serializers.ModelSerializer):
    class Meta:
        model = Activity
        fields = "__all__"

    def validate(self, data):
        destination = data["destination"]
        date = data["date"]
        cost = data["cost"]

        if date < destination.arrival_date:
            raise serializers.ValidationError(
                "L'activité ne peut pas être avant l'arrivée à destination."
            )

        if date > destination.departure_date:
            raise serializers.ValidationError(
                "L'activité ne peut pas être après le départ de la destination."
            )

        if cost < 0:
            raise serializers.ValidationError(
                "Le coût d'une activité ne peut pas être négatif."
            )

        return data


class ParticipationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Participation
        fields = "__all__"