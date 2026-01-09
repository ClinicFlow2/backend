from django.db import models
from patients.models import Patient


class Visit(models.Model):
    class SexChoices(models.TextChoices):
        MALE = "M", "Male"
        FEMALE = "F", "Female"

    patient = models.ForeignKey(Patient, on_delete=models.CASCADE, related_name="visits")

    # Visit metadata
    reason = models.CharField(max_length=255, blank=True, default="")
    notes = models.TextField(blank=True, default="")
    diagnosis = models.CharField(max_length=255, blank=True, default="")

    # Vital signs (optional, because some visits might not record everything)
    weight_kg = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    height_cm = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    temperature_c = models.DecimalField(max_digits=4, decimal_places=1, null=True, blank=True)

    # Blood pressure stored as two integers
    bp_systolic = models.PositiveSmallIntegerField(null=True, blank=True)
    bp_diastolic = models.PositiveSmallIntegerField(null=True, blank=True)

    # Especially for children
    head_circumference_cm = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"Visit #{self.id} - {self.patient} - {self.created_at.date()}"