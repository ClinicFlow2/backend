from rest_framework import generics
from rest_framework.permissions import IsAuthenticated
from .models import Patient
from .serializers import PatientSerializer


class PatientListCreateView(generics.ListCreateAPIView):
    serializer_class = PatientSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        # Only return patients created by the logged-in doctor
        return Patient.objects.filter(created_by=self.request.user).order_by("last_name", "first_name")

    def perform_create(self, serializer):
        # Force ownership (client cannot set created_by)
        serializer.save(created_by=self.request.user)


class PatientDetailView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = PatientSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        # Only allow access to the doctor's own patients
        return Patient.objects.filter(created_by=self.request.user)