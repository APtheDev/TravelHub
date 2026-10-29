from rest_framework.routers import DefaultRouter
from django.urls import path, include

from .views import (
    TripViewSet,
    DestinationViewSet,
    ActivityViewSet,
    ParticipationViewSet,
    UserViewSet,
    RegisterView
)

router = DefaultRouter()

router.register("trips", TripViewSet)
router.register("destinations", DestinationViewSet)
router.register("activities", ActivityViewSet)
router.register("participations", ParticipationViewSet)
router.register("users", UserViewSet)

urlpatterns = [
    path("", include(router.urls)),
    path("register/", RegisterView.as_view(), name="register"),
]