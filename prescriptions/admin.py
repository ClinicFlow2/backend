from django.contrib import admin
from .models import Prescription, PrescriptionItem


class PrescriptionItemInline(admin.TabularInline):
    model = PrescriptionItem
    extra = 1


@admin.register(Prescription)
class PrescriptionAdmin(admin.ModelAdmin):
    list_display = ("id", "visit", "created_at")
    list_filter = ("created_at",)
    search_fields = ("visit__patient__first_name", "visit__patient__last_name")
    inlines = [PrescriptionItemInline]


@admin.register(PrescriptionItem)
class PrescriptionItemAdmin(admin.ModelAdmin):
    list_display = ("id", "prescription", "medication_name", "dosage", "frequency", "duration")
    search_fields = ("medication_name",)