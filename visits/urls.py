from django.urls import path
from .views import (
    VisitListCreateAPIView,
    VisitDetailAPIView,
    VitalSignListCreateAPIView,
    VitalSignDetailAPIView,
)

urlpatterns = [
    path("", VisitListCreateAPIView.as_view(), name="visit-list-create"),
    path("<int:pk>/", VisitDetailAPIView.as_view(), name="visit-detail"),

    path("vitals/", VitalSignListCreateAPIView.as_view(), name="vitals-list-create"),
    path("vitals/<int:pk>/", VitalSignDetailAPIView.as_view(), name="vitals-detail"),
]