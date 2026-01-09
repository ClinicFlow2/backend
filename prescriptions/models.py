from django.db import models


class Prescription(models.Model):
    visit = models.ForeignKey(
        "visits.Visit",
        on_delete=models.CASCADE,
        related_name="prescriptions",
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    notes = models.TextField(blank=True, default="")

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"Prescription #{self.id} (Visit #{self.visit_id})"


class PrescriptionItem(models.Model):
    prescription = models.ForeignKey(
        Prescription,
        on_delete=models.CASCADE,
        related_name="items",
    )

    # Medication line
    medication_name = models.CharField(max_length=255)
    dosage = models.CharField(max_length=255, blank=True, default="")      # e.g. "500 mg"
    route = models.CharField(max_length=100, blank=True, default="")       # e.g. "PO"
    frequency = models.CharField(max_length=100, blank=True, default="")   # e.g. "2x/day"
    duration = models.CharField(max_length=100, blank=True, default="")    # e.g. "5 days"
    instructions = models.TextField(blank=True, default="")                # e.g. "After meals"

    allow_outside_purchase = models.BooleanField(
        default=False,
        help_text="Allow patient to buy outside hospital if out of stock.",
    )

    def __str__(self):
        return f"{self.medication_name} (Prescription #{self.prescription_id})"