from django.urls import path
from .views import (
    MedicationListCreateAPIView,
    PrescriptionListCreateAPIView,
    PrescriptionDetailAPIView,
    PrescriptionTemplateListAPIView,
    PrescriptionTemplateDetailAPIView,
)

urlpatterns = [
    path("templates/", PrescriptionTemplateListAPIView.as_view(), name="prescription-template-list"),
    path("templates/<int:pk>/", PrescriptionTemplateDetailAPIView.as_view(), name="prescription-template-detail"),
    path("medications/", MedicationListCreateAPIView.as_view(), name="medication-list-create"),
    path("", PrescriptionListCreateAPIView.as_view(), name="prescription-list-create"),
    path("<int:pk>/", PrescriptionDetailAPIView.as_view(), name="prescription-detail"),
]
