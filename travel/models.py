from django.db import models
from django.contrib.auth.models import User


class Trip(models.Model):

    class Status(models.TextChoices):
        PLANNED = "planned", "Planifié"
        IN_PROGRESS = "in_progress", "En cours"
        COMPLETED = "completed", "Terminé"
        CANCELLED = "cancelled", "Annulé"

    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    start_date = models.DateField()
    end_date = models.DateField()

    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.PLANNED
    )

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

    class Category(models.TextChoices):
        SIGHTSEEING = "sightseeing", "Visite touristique"
        FOOD = "food", "Restauration"
        TRANSPORT = "transport", "Transport"
        OUTDOOR = "outdoor", "Plein air"
        MUSEUM = "museum", "Musée"
        OTHER = "other", "Autre"

    name = models.CharField(max_length=200)
    description = models.TextField(blank=True)

    category = models.CharField(
        max_length=20,
        choices=Category.choices,
        default=Category.OTHER
    )

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

    class Role(models.TextChoices):
        ORGANIZER = "organizer", "Organisateur"
        PARTICIPANT = "participant", "Participant"

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

    role = models.CharField(
        max_length=20,
        choices=Role.choices,
        default=Role.PARTICIPANT
    )

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