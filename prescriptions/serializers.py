from rest_framework import serializers
from .models import Prescription, PrescriptionItem


class PrescriptionItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = PrescriptionItem
        fields = [
            "id",
            "medication_name",
            "dosage",
            "route",
            "frequency",
            "duration",
            "instructions",
            "allow_outside_purchase",
        ]
        read_only_fields = ["id"]


class PrescriptionSerializer(serializers.ModelSerializer):
    # ✅ Allow nested write
    items = PrescriptionItemSerializer(many=True)

    class Meta:
        model = Prescription
        fields = [
            "id",
            "visit",
            "notes",
            "items",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]

    def create(self, validated_data):
        items_data = validated_data.pop("items", [])
        prescription = Prescription.objects.create(**validated_data)

        # bulk create items
        PrescriptionItem.objects.bulk_create(
            [PrescriptionItem(prescription=prescription, **item) for item in items_data]
        )

        return prescription

    def update(self, instance, validated_data):
        """
        Simple, safe behavior:
        - Updates Prescription fields
        - If 'items' is provided, replace all items (delete + recreate)
        """
        items_data = validated_data.pop("items", None)

        # update prescription fields
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()

        # replace items if provided
        if items_data is not None:
            instance.items.all().delete()
            PrescriptionItem.objects.bulk_create(
                [PrescriptionItem(prescription=instance, **item) for item in items_data]
            )

        return instance