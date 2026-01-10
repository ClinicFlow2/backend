from rest_framework import serializers
from .models import Medication, Prescription, PrescriptionItem


class MedicationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Medication
        fields = ["id", "name", "form", "strength", "is_active"]


# -------- Items (WRITE) --------
class PrescriptionItemWriteSerializer(serializers.ModelSerializer):
    class Meta:
        model = PrescriptionItem
        fields = [
            "medication",  # FK id
            "dosage",
            "route",
            "frequency",
            "duration",
            "instructions",
            "allow_outside_purchase",
        ]


# -------- Items (READ) --------
class PrescriptionItemReadSerializer(serializers.ModelSerializer):
    medication = MedicationSerializer()

    class Meta:
        model = PrescriptionItem
        fields = [
            "id",
            "medication",
            "dosage",
            "route",
            "frequency",
            "duration",
            "instructions",
            "allow_outside_purchase",
        ]


# -------- Prescription (WRITE) --------
class PrescriptionSerializer(serializers.ModelSerializer):
    items = PrescriptionItemWriteSerializer(many=True)

    class Meta:
        model = Prescription
        fields = [
            "id",
            "visit",
            "template_used",
            "notes",
            "items",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]

    def create(self, validated_data):
        items_data = validated_data.pop("items", [])
        prescription = Prescription.objects.create(**validated_data)

        PrescriptionItem.objects.bulk_create(
            [PrescriptionItem(prescription=prescription, **item) for item in items_data]
        )

        return prescription

    def update(self, instance, validated_data):
        items_data = validated_data.pop("items", None)

        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()

        if items_data is not None:
            instance.items.all().delete()
            PrescriptionItem.objects.bulk_create(
                [PrescriptionItem(prescription=instance, **item) for item in items_data]
            )

        return instance


# -------- Prescription (READ detail) --------
class PrescriptionDetailSerializer(serializers.ModelSerializer):
    items = PrescriptionItemReadSerializer(many=True)

    class Meta:
        model = Prescription
        fields = [
            "id",
            "visit",
            "template_used",
            "notes",
            "items",
            "created_at",
            "updated_at",
        ]