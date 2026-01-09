from rest_framework import serializers
from .models import Visit


class VisitSerializer(serializers.ModelSerializer):
    class Meta:
        model = Visit
        fields = [
            "id",
            "patient",
            "reason",
            "notes",
            "diagnosis",
            "weight_kg",
            "height_cm",
            "temperature_c",
            "bp_systolic",
            "bp_diastolic",
            "head_circumference_cm",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["created_at", "updated_at"] 