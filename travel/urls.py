from rest_framework.routers import DefaultRouter
from .views import (
    TripViewSet,
    DestinationViewSet,
    ActivityViewSet,
    ParticipationViewSet,
)

router = DefaultRouter()

router.register("trips", TripViewSet)
router.register("destinations", DestinationViewSet)
router.register("activities", ActivityViewSet)
router.register("participations", ParticipationViewSet)

urlpatterns = router.urls