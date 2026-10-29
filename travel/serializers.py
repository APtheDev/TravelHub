from rest_framework import serializers
from .models import Trip, Destination, Activity, Participation
from django.contrib.auth.models import User

class TripSerializer(serializers.ModelSerializer):
    class Meta:
        model = Trip
        fields = "__all__"
        read_only_fields = ["owner"]

    def validate(self, data):
        start_date = data.get("start_date")
        end_date = data.get("end_date")

        if self.instance:
            if start_date is None:
                start_date = self.instance.start_date

            if end_date is None:
                end_date = self.instance.end_date

        if start_date and end_date and start_date > end_date:
            raise serializers.ValidationError(
                "La date de début doit être avant la date de fin."
            )
        if self.instance:
            destinations = self.instance.destinations.all()

            for destination in destinations:
                if (
                    destination.arrival_date < start_date
                    or destination.departure_date > end_date
                ):
                    raise serializers.ValidationError(
                        "Les nouvelles dates du voyage ne peuvent pas exclure une destination existante."
                    )
        return data


class DestinationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Destination
        fields = "__all__"

    def validate(self, data):
        trip = data.get("trip")
        arrival_date = data.get("arrival_date")
        departure_date = data.get("departure_date")

        if self.instance:
            if trip is None:
                trip = self.instance.trip

            if arrival_date is None:
                arrival_date = self.instance.arrival_date

            if departure_date is None:
                departure_date = self.instance.departure_date

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
        if self.instance:
            activities = self.instance.activities.all()

            for activity in activities:
                if activity.date < arrival_date or activity.date > departure_date:
                    raise serializers.ValidationError(
                        "Les nouvelles dates de la destination ne peuvent pas exclure une activité existante."
                    )
        return data


class ActivitySerializer(serializers.ModelSerializer):
    class Meta:
        model = Activity
        fields = "__all__"

    def validate(self, data):
        destination = data.get("destination")
        date = data.get("date")
        cost = data.get("cost")

        if self.instance:
            if destination is None:
                destination = self.instance.destination

            if date is None:
                date = self.instance.date

            if cost is None:
                cost = self.instance.cost

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

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ["id", "username"]

class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, min_length=8)
    password_confirm = serializers.CharField(write_only=True)

    class Meta:
        model = User
        fields = ["id", "username", "email", "password", "password_confirm"]

    def validate(self, data):
        if data["password"] != data["password_confirm"]:
            raise serializers.ValidationError(
                "Les mots de passe ne correspondent pas."
            )

        return data

    def create(self, validated_data):
        validated_data.pop("password_confirm")

        return User.objects.create_user(**validated_data)