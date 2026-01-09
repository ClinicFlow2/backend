from rest_framework import generics
from rest_framework.permissions import IsAuthenticated
from .models import Visit
from .serializers import VisitSerializer


class VisitListCreateView(generics.ListCreateAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = VisitSerializer

    def get_queryset(self):
        queryset = Visit.objects.select_related("patient").all()

        # Optional filter: /api/visits/?patient_id=1
        patient_id = self.request.query_params.get("patient_id")
        if patient_id:
            queryset = queryset.filter(patient_id=patient_id)

        return queryset


class VisitDetailView(generics.RetrieveUpdateDestroyAPIView):
    permission_classes = [IsAuthenticated]
    queryset = Visit.objects.select_related("patient").all()
    serializer_class = VisitSerializer