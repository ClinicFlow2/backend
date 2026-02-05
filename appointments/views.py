from io import StringIO

from django.conf import settings
from django.core.management import call_command
from django.utils import timezone
from django.contrib.auth import get_user_model
from django.http import HttpResponse
from django.views import View

from rest_framework import generics, permissions
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import Appointment
from .serializers import AppointmentSerializer, DoctorSerializer

User = get_user_model()


class TriggerSmsRemindersView(View):
    """
    Cron endpoint to trigger SMS reminders.
    Protected by a secret token passed as query param: ?token=YOUR_CRON_SECRET
    """

    def get(self, request):
        # Verify the secret token
        token = request.GET.get("token", "")
        expected_token = getattr(settings, "CRON_SECRET_TOKEN", "")

        if not expected_token or token != expected_token:
            return HttpResponse("Unauthorized", status=401)

        # Run the management command and capture output
        output = StringIO()
        try:
            call_command("send_appointment_reminders", stdout=output)
            result = output.getvalue()
            return HttpResponse(f"OK\n{result}", status=200, content_type="text/plain")
        except Exception as e:
            return HttpResponse(f"Error: {str(e)}", status=500, content_type="text/plain")


class DoctorListAPIView(APIView):
    """List users with doctor or nurse role for appointment assignment."""
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        # Get users who have a profile with role 'doctor' or 'nurse' (exclude admin)
        doctors = User.objects.filter(
            profile__role__in=['doctor', 'nurse']
        ).select_related('profile').order_by('first_name', 'last_name')
        serializer = DoctorSerializer(doctors, many=True)
        return Response(serializer.data)


class AppointmentListCreateAPIView(generics.ListCreateAPIView):
    serializer_class = AppointmentSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        """
        All authenticated staff can see all appointments.
        Optional filters: ?patient=<id>, ?status=<status>, ?upcoming=true
        """
        qs = (
            Appointment.objects.select_related("patient", "visit", "doctor", "doctor__profile")
            .order_by("-scheduled_at")
        )

        patient_id = self.request.query_params.get("patient")
        status_ = self.request.query_params.get("status")
        upcoming = self.request.query_params.get("upcoming")

        if patient_id:
            qs = qs.filter(patient_id=patient_id)

        if status_:
            qs = qs.filter(status=status_)

        if upcoming and upcoming.lower() == "true":
            qs = qs.filter(scheduled_at__gte=timezone.now()).exclude(
                status__in=["CANCELLED", "COMPLETED", "NO_SHOW"]
            )

        return qs

class AppointmentDetailAPIView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = AppointmentSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        # All authenticated staff can access any appointment
        return Appointment.objects.select_related("patient", "visit", "doctor", "doctor__profile")
