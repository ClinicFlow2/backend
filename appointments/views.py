from django.utils import timezone
from rest_framework import generics, permissions
from .models import Appointment
from .serializers import AppointmentSerializer


class AppointmentListCreateAPIView(generics.ListCreateAPIView):
    serializer_class = AppointmentSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        qs = Appointment.objects.select_related("patient", "visit").all()

        # Filters (optional)
        patient_id = self.request.query_params.get("patient")
        status_ = self.request.query_params.get("status")
        upcoming = self.request.query_params.get("upcoming")  # "true" / "false"

        if patient_id:
            qs = qs.filter(patient_id=patient_id)

        if status_:
            qs = qs.filter(status=status_)

        if upcoming and upcoming.lower() == "true":
            qs = qs.filter(scheduled_at__gte=timezone.now()).exclude(status__in=["CANCELLED", "COMPLETED", "NO_SHOW"])

        return qs


class AppointmentDetailAPIView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Appointment.objects.select_related("patient", "visit").all()
    serializer_class = AppointmentSerializer
    permission_classes = [permissions.IsAuthenticated]