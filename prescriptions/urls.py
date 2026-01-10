from django.urls import path
from .views import (
    MedicationListCreateAPIView,
    PrescriptionListCreateAPIView,
    PrescriptionDetailAPIView,
)

urlpatterns = [
    path("medications/", MedicationListCreateAPIView.as_view(), name="medication-list-create"),
    path("", PrescriptionListCreateAPIView.as_view(), name="prescription-list-create"),
    path("<int:pk>/", PrescriptionDetailAPIView.as_view(), name="prescription-detail"),
]