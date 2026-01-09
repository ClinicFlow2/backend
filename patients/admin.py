from django.contrib import admin
from .models import Patient


@admin.register(Patient)
class PatientAdmin(admin.ModelAdmin):
    list_display = (
        "last_name",
        "first_name",
        "sex",
        "date_of_birth",
        "phone",
        "is_active",
    )
    search_fields = ("first_name", "last_name", "phone")
    list_filter = ("sex", "is_active")