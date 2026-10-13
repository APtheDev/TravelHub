from rest_framework import serializers
from .models import Trip, Destination, Activity, Participation


class TripSerializer(serializers.ModelSerializer):
    class Meta:
        model = Trip
        fields = "__all__"

    def validate(self, data):
        start_date = data["start_date"]
        
    
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
        if arrival_date > trip.end_date:
            raise serializers.ValidationError(
                "La destination doit etre dans les dates du voyage."
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


class ParticipationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Participation
        fields = "__all__"