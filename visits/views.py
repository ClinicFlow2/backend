from rest_framework import generics, permissions
from .models import Visit, VitalSign
from .serializers import VisitSerializer, VitalSignSerializer


class VisitListCreateAPIView(generics.ListCreateAPIView):
    queryset = Visit.objects.select_related("patient").all()
    serializer_class = VisitSerializer
    permission_classes = [permissions.IsAuthenticated]


class VisitDetailAPIView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Visit.objects.select_related("patient").all()
    serializer_class = VisitSerializer
    permission_classes = [permissions.IsAuthenticated]


class VitalSignListCreateAPIView(generics.ListCreateAPIView):
    queryset = VitalSign.objects.select_related("visit", "visit__patient").all()
    serializer_class = VitalSignSerializer
    permission_classes = [permissions.IsAuthenticated]


class VitalSignDetailAPIView(generics.RetrieveUpdateDestroyAPIView):
    queryset = VitalSign.objects.select_related("visit", "visit__patient").all()
    serializer_class = VitalSignSerializer
    permission_classes = [permissions.IsAuthenticated]