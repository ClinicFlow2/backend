# visits/views.py
from rest_framework import generics, permissions
from rest_framework.exceptions import PermissionDenied

from .models import Visit, VitalSign
from .serializers import VisitSerializer, VitalSignSerializer


class VisitListCreateAPIView(generics.ListCreateAPIView):
    serializer_class = VisitSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        """
        All authenticated staff can see all visits.
        Optional filter: ?patient=<patient_id>
        """
        qs = (
            Visit.objects.select_related("patient", "patient__created_by")
            .order_by("-visit_date")
        )

        patient_id = self.request.query_params.get("patient")
        if patient_id:
            qs = qs.filter(patient_id=patient_id)

        return qs

    def perform_create(self, serializer):
        """
        Any authenticated user can create a visit for any patient.
        """
        patient = serializer.validated_data.get("patient")
        if not patient:
            raise PermissionDenied("Patient is required.")

        serializer.save()


class VisitDetailAPIView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = VisitSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        # All authenticated staff can access any visit
        return Visit.objects.select_related("patient", "patient__created_by")


class VitalSignListCreateAPIView(generics.ListCreateAPIView):
    serializer_class = VitalSignSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        """
        All authenticated staff can see all vitals.
        Optional filter: ?visit=<visit_id>
        """
        qs = (
            VitalSign.objects.select_related(
                "visit",
                "visit__patient",
                "visit__patient__created_by",
            )
            .order_by("-measured_at")
        )

        visit_id = self.request.query_params.get("visit")
        if visit_id:
            qs = qs.filter(visit_id=visit_id)

        return qs

    def perform_create(self, serializer):
        """
        Any authenticated user can add vitals to any visit.
        """
        visit = serializer.validated_data.get("visit")
        if not visit:
            raise PermissionDenied("Visit is required.")

        serializer.save()


class VitalSignDetailAPIView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = VitalSignSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        # All authenticated staff can access any vital sign
        return VitalSign.objects.select_related(
            "visit",
            "visit__patient",
            "visit__patient__created_by",
        )
