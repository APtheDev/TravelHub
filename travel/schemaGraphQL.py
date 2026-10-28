import graphene
from graphene_django import DjangoObjectType
from graphql import GraphQLError
from .serializers import TripSerializer, DestinationSerializer, ActivitySerializer
from django.contrib.auth.models import User
from .models import Trip, Destination, Activity, Participation
from django.db import transaction


class ActivityType(DjangoObjectType):
    class Meta:
        model = Activity
        fields = (
            "id",
            "name",
            "description",
            "category",
            "date",
            "cost",
        )
        convert_choices_to_enum = False


class DestinationType(DjangoObjectType):

    activities = graphene.List(ActivityType)

    class Meta:
        model = Destination
        fields = (
            "id",
            "city",
            "country",
            "arrival_date",
            "departure_date",
        )

    @staticmethod
    def resolve_activities(destination: Destination, info):
        user = info.context.user

        if not user.is_authenticated:
            return Activity.objects.none()

        return Activity.objects.filter(
            destination=destination, destination__trip__owner=user
        )


class TripType(DjangoObjectType):

    destinations = graphene.List(DestinationType)

    class Meta:
        model = Trip
        fields = (
            "id",
            "title",
            "description",
            "start_date",
            "end_date",
            "status",
        )
        convert_choices_to_enum = False

    @staticmethod
    def resolve_destinations(trip: Trip, info):
        user = info.context.user

        if not user.is_authenticated:
            return Destination.objects.none()

        return Destination.objects.filter(trip=trip, trip__owner=user)


class ParticipationType(DjangoObjectType):

    username = graphene.String()

    class Meta:
        model = Participation
        fields = (
            "id",
            "role",
            "joined_at",
        )
        convert_choices_to_enum = False

    @staticmethod
    def resolve_username(participation: Participation, info):
        return participation.user.username


class Query(graphene.ObjectType):

    hello = graphene.String()

    trips = graphene.List(TripType)

    trip = graphene.Field(TripType, id=graphene.Int(required=True))

    participations = graphene.List(
        ParticipationType, trip_id=graphene.Int(required=True)
    )

    def resolve_hello(root, info):
        return "Pong"

    def resolve_trips(root, info):
        user = info.context.user

        if not user.is_authenticated:
            return Trip.objects.none()

        return Trip.objects.filter(owner=user).prefetch_related(
            "destinations__activities"
        )

    def resolve_trip(root, info, id):
        user = info.context.user

        if not user.is_authenticated:
            return None

        return (
            Trip.objects.filter(id=id, owner=user)
            .prefetch_related("destinations__activities")
            .first()
        )

    @staticmethod
    def resolve_participations(root, info, trip_id):
        user = info.context.user

        if not user.is_authenticated:
            return Participation.objects.none()

        return Participation.objects.filter(
            trip_id=trip_id, trip__owner=user
        ).select_related("user")


class CreateTrip(graphene.Mutation):

    class Arguments:
        title = graphene.String(required=True)
        description = graphene.String()
        start_date = graphene.Date(required=True)
        end_date = graphene.Date(required=True)
        status = graphene.String(default_value="planned")

    # Données retournées après la création
    trip = graphene.Field(TripType)
    ok = graphene.Boolean(required=True)

    @staticmethod
    @transaction.atomic
    def mutate(
        root, info, title, start_date, end_date, description="", status="planned"
    ):
        user = info.context.user

        if not user.is_authenticated:
            raise GraphQLError("Authentification requise.")

        serializer = TripSerializer(
            data={
                "title": title,
                "description": description,
                "start_date": start_date.isoformat(),
                "end_date": end_date.isoformat(),
                "status": status,
            }
        )

        if not serializer.is_valid():
            raise GraphQLError(str(serializer.errors))

        trip = serializer.save(owner=user)

        Participation.objects.get_or_create(
            user=user,
            trip=trip,
            defaults={"role": Participation.Role.ORGANIZER},
        )

        return CreateTrip(trip=trip, ok=True)


class UpdateTrip(graphene.Mutation):

    class Arguments:
        id = graphene.Int(required=True)
        title = graphene.String()
        description = graphene.String()
        start_date = graphene.Date()
        end_date = graphene.Date()
        status = graphene.String()

    trip = graphene.Field(TripType)
    ok = graphene.Boolean(required=True)

    @staticmethod
    def mutate(
        root,
        info,
        id,
        title=None,
        start_date=None,
        end_date=None,
        description=None,
        status=None,
    ):
        user = info.context.user

        if not user.is_authenticated:
            raise GraphQLError("Authentification requise")

        trip = Trip.objects.filter(id=id, owner=user).first()

        if trip is None:
            raise GraphQLError("Voyage introuvable.")

        data = {
            "title": trip.title if title is None else title,
            "description": (trip.description if description is None else description),
            "start_date": (
                trip.start_date if start_date is None else start_date
            ).isoformat(),
            "end_date": (trip.end_date if end_date is None else end_date).isoformat(),
            "status": (trip.status if status is None else status),
        }

        serializer = TripSerializer(instance=trip, data=data)

        if not serializer.is_valid():
            raise GraphQLError(str(serializer.errors))

        updated_trip = serializer.save()

        return UpdateTrip(trip=updated_trip, ok=True)


class DeleteTrip(graphene.Mutation):
    class Arguments:
        id = graphene.Int(required=True)

    ok = graphene.Boolean(required=True)
    deleted_id = graphene.Int(required=True)

    @staticmethod
    def mutate(root, info, id):

        user = info.context.user

        if not user.is_authenticated:
            raise GraphQLError("Authentification requise")

        trip = Trip.objects.filter(id=id, owner=user).first()

        if trip is None:
            raise GraphQLError("Le Voyage est Introuvable ou l'accès est refusé ! :(")

        trip.delete()

        return DeleteTrip(ok=True, deleted_id=id)


class CreateDestination(graphene.Mutation):

    class Arguments:
        trip_id = graphene.Int(required=True)
        city = graphene.String(required=True)
        country = graphene.String(required=True)
        arrival_date = graphene.Date(required=True)
        departure_date = graphene.Date(required=True)

    destination = graphene.Field(DestinationType)
    ok = graphene.Boolean(required=True)

    @staticmethod
    def mutate(root, info, trip_id, city, country, arrival_date, departure_date):
        user = info.context.user

        if not user.is_authenticated:
            raise GraphQLError("Authentification requise.")

        trip = Trip.objects.filter(id=trip_id, owner=user).first()

        if trip is None:
            raise GraphQLError("Voyage introuvable ou accès refusé.")

        data = {
            "city": city,
            "country": country,
            "arrival_date": arrival_date.isoformat(),
            "departure_date": departure_date.isoformat(),
            "trip": trip.id,
        }

        serializer = DestinationSerializer(data=data)

        if not serializer.is_valid():
            raise GraphQLError(str(serializer.errors))

        destination = serializer.save()

        return CreateDestination(destination=destination, ok=True)


class UpdateDestination(graphene.Mutation):

    class Arguments:
        id = graphene.Int(required=True)
        city = graphene.String()
        country = graphene.String()
        arrival_date = graphene.Date()
        departure_date = graphene.Date()

    destination = graphene.Field(DestinationType)
    ok = graphene.Boolean(required=True)

    @staticmethod
    def mutate(
        root, info, id, city=None, country=None, arrival_date=None, departure_date=None
    ):

        user = info.context.user

        if not user.is_authenticated:
            raise GraphQLError("Authentification requise.")

        destination = Destination.objects.filter(id=id, trip__owner=user).first()

        if destination is None:
            raise GraphQLError("Destination introuvable ou accès refusé.")

        data = {
            "city": (destination.city if city is None else city),
            "country": (destination.country if country is None else country),
            "arrival_date": (
                destination.arrival_date if arrival_date is None else arrival_date
            ).isoformat(),
            "departure_date": (
                destination.departure_date if departure_date is None else departure_date
            ).isoformat(),
            "trip": destination.trip_id,
        }

        serializer = DestinationSerializer(instance=destination, data=data)

        if not serializer.is_valid():
            raise GraphQLError(str(serializer.errors))

        updated_destination = serializer.save()

        return UpdateDestination(destination=updated_destination, ok=True)


class DeleteDestination(graphene.Mutation):

    class Arguments:
        id = graphene.Int(required=True)

    ok = graphene.Boolean(required=True)
    deleted_id = graphene.Int(required=True)

    @staticmethod
    def mutate(root, info, id):

        user = info.context.user

        if not user.is_authenticated:
            raise GraphQLError("Authentification requise.")

        destination = Destination.objects.filter(id=id, trip__owner=user).first()

        if destination is None:
            raise GraphQLError("Destination introuvable ou accès refusé.")

        destination.delete()

        return DeleteDestination(ok=True, deleted_id=id)


class CreateActivity(graphene.Mutation):

    class Arguments:
        destination_id = graphene.Int(required=True)
        name = graphene.String(required=True)
        description = graphene.String(default_value="")
        category = graphene.String(default_value="other")
        date = graphene.Date(required=True)
        cost = graphene.Decimal(required=True)

    activity = graphene.Field(ActivityType)
    ok = graphene.Boolean(required=True)

    @staticmethod
    def mutate(
        root, info, destination_id, name, date, cost, description="", category="other"
    ):
        user = info.context.user

        if not user.is_authenticated:
            raise GraphQLError("Authentification requise.")

        destination = Destination.objects.filter(
            id=destination_id, trip__owner=user
        ).first()

        if destination is None:
            raise GraphQLError("Destination introuvable ou accès refusé.")

        data = {
            "name": name,
            "description": description,
            "category": category,
            "date": date.isoformat(),
            "cost": str(cost),
            "destination": destination.id,
        }

        serializer = ActivitySerializer(data=data)

        if not serializer.is_valid():
            raise GraphQLError(str(serializer.errors))

        activity = serializer.save()

        return CreateActivity(activity=activity, ok=True)


class UpdateActivity(graphene.Mutation):

    class Arguments:
        id = graphene.Int(required=True)
        name = graphene.String()
        description = graphene.String()
        category = graphene.String()
        date = graphene.Date()
        cost = graphene.Decimal()
        destination_id = graphene.Int()

    activity = graphene.Field(ActivityType)
    ok = graphene.Boolean(required=True)

    @staticmethod
    def mutate(
        root,
        info,
        id,
        name=None,
        description=None,
        category=None,
        date=None,
        cost=None,
        destination_id=None,
    ):
        user = info.context.user

        if not user.is_authenticated:
            raise GraphQLError("Authentification requise.")

        activity = Activity.objects.filter(id=id, destination__trip__owner=user).first()

        if activity is None:
            raise GraphQLError("Activité introuvable ou accès refusé.")

        new_destination_id = (
            activity.destination_id if destination_id is None else destination_id
        )

        destination = Destination.objects.filter(
            id=new_destination_id, trip__owner=user
        ).first()

        if destination is None:
            raise GraphQLError("Destination introuvable ou accès refusé.")

        data = {
            "name": (activity.name if name is None else name),
            "description": (
                activity.description if description is None else description
            ),
            "category": (activity.category if category is None else category),
            "date": (activity.date if date is None else date).isoformat(),
            "cost": str(activity.cost if cost is None else cost),
            "destination": destination.id,
        }

        serializer = ActivitySerializer(instance=activity, data=data)

        if not serializer.is_valid():
            raise GraphQLError(str(serializer.errors))

        updated_activity = serializer.save()

        return UpdateActivity(activity=updated_activity, ok=True)


class DeleteActivity(graphene.Mutation):

    class Arguments:
        id = graphene.Int(required=True)

    ok = graphene.Boolean(required=True)
    deleted_id = graphene.Int(required=True)

    @staticmethod
    def mutate(root, info, id):
        user = info.context.user

        if not user.is_authenticated:
            raise GraphQLError("Authentification requise.")

        activity = Activity.objects.filter(id=id, destination__trip__owner=user).first()

        if activity is None:
            raise GraphQLError("Activité introuvable ou accès refusé.")

        activity.delete()

        return DeleteActivity(ok=True, deleted_id=id)


class CreateParticipation(graphene.Mutation):

    class Arguments:
        trip_id = graphene.Int(required=True)
        username = graphene.String(required=True)

    participation = graphene.Field(ParticipationType)
    ok = graphene.Boolean(required=True)

    @staticmethod
    def mutate(root, info, trip_id, username):

        user = info.context.user
        if not user.is_authenticated:
            raise GraphQLError("Authentification requise.")
        trip = Trip.objects.filter(id=trip_id, owner=user).first()

        if trip is None:
            raise GraphQLError("Voyage introuvable ou accès refusé.")

        participant = User.objects.filter(username=username, is_active=True).first()

        if participant is None:
            raise GraphQLError("Utilisateur introuvable.")

        participation, created = Participation.objects.get_or_create(
            user=participant,
            trip=trip,
            defaults={"role": Participation.Role.PARTICIPANT},
        )

        if not created:
            raise GraphQLError("Cet utilisateur participe déjà au voyage.")

        return CreateParticipation(participation=participation, ok=True)


class UpdateParticipation(graphene.Mutation):

    class Arguments:
        id = graphene.Int(required=True)
        role = graphene.String(required=True)

    participation = graphene.Field(ParticipationType)
    ok = graphene.Boolean(required=True)

    @staticmethod
    def mutate(root, info, id, role):
        user = info.context.user

        if not user.is_authenticated:
            raise GraphQLError("Authentification requise.")

        participation = (
            Participation.objects.filter(id=id, trip__owner=user)
            .select_related("trip", "user")
            .first()
        )

        if participation is None:
            raise GraphQLError("Participation introuvable ou accès refusé.")

        if role not in Participation.Role.values:
            raise GraphQLError("Rôle invalide.")

        if participation.user_id == participation.trip.owner_id:
            raise GraphQLError("Impossible de modifier le rôle du propriétaire.")

        participation.role = role
        participation.save(update_fields=["role"])

        return UpdateParticipation(participation=participation, ok=True)


class DeleteParticipation(graphene.Mutation):

    class Arguments:
        id = graphene.Int(required=True)

    ok = graphene.Boolean(required=True)
    deleted_id = graphene.Int(required=True)

    @staticmethod
    def mutate(root, info, id):
        user = info.context.user

        if not user.is_authenticated:
            raise GraphQLError("Authentification requise.")

        participation = (
            Participation.objects.filter(id=id, trip__owner=user)
            .select_related("trip")
            .first()
        )

        if participation is None:
            raise GraphQLError("Participation introuvable ou accès refusé.")

        if participation.user_id == participation.trip.owner_id:
            raise GraphQLError("Impossible de retirer le propriétaire.")

        participation.delete()

        return DeleteParticipation(ok=True, deleted_id=id)


class Mutation(graphene.ObjectType):
    create_trip = CreateTrip.Field()
    update_trip = UpdateTrip.Field()
    delete_trip = DeleteTrip.Field()

    create_destination = CreateDestination.Field()
    update_destination = UpdateDestination.Field()
    delete_destination = DeleteDestination.Field()

    create_activity = CreateActivity.Field()
    update_activity = UpdateActivity.Field()
    delete_activity = DeleteActivity.Field()

    create_participation = CreateParticipation.Field()
    update_participation = UpdateParticipation.Field()
    delete_participation = DeleteParticipation.Field()


schema = graphene.Schema(query=Query, mutation=Mutation)
