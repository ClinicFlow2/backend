from rest_framework import generics, permissions
from .models import Prescription, Medication
from .serializers import (
    MedicationSerializer,
    PrescriptionSerializer,
    PrescriptionDetailSerializer,
)


class MedicationListCreateAPIView(generics.ListCreateAPIView):
    queryset = Medication.objects.all()
    serializer_class = MedicationSerializer
    permission_classes = [permissions.IsAuthenticated]


class PrescriptionListCreateAPIView(generics.ListCreateAPIView):
    queryset = (
        Prescription.objects
        .select_related("visit", "visit__patient", "template_used")
        .prefetch_related("items__medication")
        .all()
    )
    serializer_class = PrescriptionSerializer
    permission_classes = [permissions.IsAuthenticated]


class PrescriptionDetailAPIView(generics.RetrieveUpdateDestroyAPIView):
    queryset = (
        Prescription.objects
        .select_related("visit", "visit__patient", "template_used")
        .prefetch_related("items__medication")
        .all()
    )
    permission_classes = [permissions.IsAuthenticated]

    def get_serializer_class(self):
        if self.request.method == "GET":
            return PrescriptionDetailSerializer
        return PrescriptionSerializer