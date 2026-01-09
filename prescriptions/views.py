from rest_framework import generics, permissions
from .models import Prescription, PrescriptionItem
from .serializers import PrescriptionSerializer, PrescriptionItemSerializer


class PrescriptionListCreateAPIView(generics.ListCreateAPIView):
    queryset = Prescription.objects.select_related("visit", "visit__patient").all()
    serializer_class = PrescriptionSerializer
    permission_classes = [permissions.IsAuthenticated]


class PrescriptionDetailAPIView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Prescription.objects.select_related("visit", "visit__patient").all()
    serializer_class = PrescriptionSerializer
    permission_classes = [permissions.IsAuthenticated]


class PrescriptionItemListCreateAPIView(generics.ListCreateAPIView):
    queryset = PrescriptionItem.objects.select_related("prescription", "prescription__visit").all()
    serializer_class = PrescriptionItemSerializer
    permission_classes = [permissions.IsAuthenticated]


class PrescriptionItemDetailAPIView(generics.RetrieveUpdateDestroyAPIView):
    queryset = PrescriptionItem.objects.select_related("prescription", "prescription__visit").all()
    serializer_class = PrescriptionItemSerializer
    permission_classes = [permissions.IsAuthenticated]