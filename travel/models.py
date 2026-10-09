from django.db import models
from django.contrib.auth.models import User


class Trip(models.Model):
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    start_date = models.DateField()
    end_date = models.DateField()
    status = models.CharField(max_length=50)

    owner = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="owned_trips"
    )

    participants = models.ManyToManyField(
        User,
        through="Participation",
        related_name="trips",
        blank=True
    )

    def __str__(self):
        return self.title


class Destination(models.Model):
    city = models.CharField(max_length=100)
    country = models.CharField(max_length=100)
    arrival_date = models.DateField()
    departure_date = models.DateField()

    trip = models.ForeignKey(
        Trip,
        on_delete=models.CASCADE,
        related_name="destinations"
    )

    def __str__(self):
        return f"{self.city}, {self.country}"


class Activity(models.Model):
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    category = models.CharField(max_length=100)
    date = models.DateField()

    cost = models.DecimalField(
        max_digits=10,
        decimal_places=2
    )

    destination = models.ForeignKey(
        Destination,
        on_delete=models.CASCADE,
        related_name="activities"
    )

    def __str__(self):
        return self.name


class Participation(models.Model):
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="participations"
    )

    trip = models.ForeignKey(
        Trip,
        on_delete=models.CASCADE,
        related_name="participations"
    )

    role = models.CharField(max_length=50)
    joined_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["user", "trip"],
                name="unique_user_trip"
            )
        ]

    def __str__(self):
        return f"{self.user.username} - {self.trip.title}"