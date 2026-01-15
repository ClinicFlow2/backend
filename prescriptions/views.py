from rest_framework import generics, permissions
from .models import Prescription, Medication, PrescriptionTemplate
from .serializers import (
    MedicationSerializer,
    PrescriptionSerializer,
    PrescriptionDetailSerializer,
    PrescriptionTemplateSerializer,
    PrescriptionTemplateDetailSerializer,
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
    permission_classes = [permissions.IsAuthenticated]

    def get_serializer_class(self):
        # ✅ GET list should return READ shape with medication details
        if self.request.method == "GET":
            return PrescriptionDetailSerializer
        return PrescriptionSerializer


class PrescriptionDetailAPIView(generics.RetrieveUpdateDestroyAPIView):
    queryset = (
        Prescription.objects
        .select_related("visit", "visit__patient", "template_used")
        .prefetch_related("items__medication")
        .all()
    )
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = PrescriptionSerializer  # ✅ safe default

    def get_serializer_class(self):
        if self.request.method == "GET":
            return PrescriptionDetailSerializer
        return PrescriptionSerializer


class PrescriptionTemplateListAPIView(generics.ListAPIView):
    queryset = PrescriptionTemplate.objects.prefetch_related("items__medication").all()
    serializer_class = PrescriptionTemplateSerializer
    permission_classes = [permissions.IsAuthenticated]


class PrescriptionTemplateDetailAPIView(generics.RetrieveAPIView):
    queryset = PrescriptionTemplate.objects.prefetch_related("items__medication").all()
    serializer_class = PrescriptionTemplateDetailSerializer
    permission_classes = [permissions.IsAuthenticated]
