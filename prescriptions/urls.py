from django.urls import path
from .views import (
    PrescriptionListCreateAPIView,
    PrescriptionDetailAPIView,
    PrescriptionItemListCreateAPIView,
    PrescriptionItemDetailAPIView,
)

urlpatterns = [
    path("", PrescriptionListCreateAPIView.as_view(), name="prescription-list-create"),
    path("<int:pk>/", PrescriptionDetailAPIView.as_view(), name="prescription-detail"),

    path("items/", PrescriptionItemListCreateAPIView.as_view(), name="prescription-item-list-create"),
    path("items/<int:pk>/", PrescriptionItemDetailAPIView.as_view(), name="prescription-item-detail"),
]