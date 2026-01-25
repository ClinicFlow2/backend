from django.urls import path
from .views import (
    VisitListCreateAPIView,
    VisitDetailAPIView,
    VitalSignListCreateAPIView,
    VitalSignDetailAPIView,
    visit_summary_pdf,
)

urlpatterns = [
    path("", VisitListCreateAPIView.as_view(), name="visit-list-create"),
    path("<int:pk>/", VisitDetailAPIView.as_view(), name="visit-detail"),
    path("<int:pk>/pdf/", visit_summary_pdf, name="visit-summary-pdf"),

    path("vitals/", VitalSignListCreateAPIView.as_view(), name="vitals-list-create"),
    path("vitals/<int:pk>/", VitalSignDetailAPIView.as_view(), name="vitals-detail"),
]