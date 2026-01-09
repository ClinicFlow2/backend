from django.conf import settings
from django.db import models


class Patient(models.Model):
    SEX_CHOICES = [
        ("M", "Male"),
        ("F", "Female"),
    ]

    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    sex = models.CharField(max_length=1, choices=SEX_CHOICES)
    date_of_birth = models.DateField()

    # Phone is optional (child may not have one)
    phone = models.CharField(max_length=30, blank=True)

    # Address is required
    address = models.TextField()

    is_active = models.BooleanField(default=True)

    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="patients",
    )

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["last_name", "first_name"]

    def __str__(self):
        return f"{self.last_name} {self.first_name}"
