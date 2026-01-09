from django.contrib import admin
from .models import Visit, VitalSign


class VitalSignInline(admin.TabularInline):
    model = VitalSign
    extra = 1
    ordering = ("-measured_at",)


@admin.register(Visit)
class VisitAdmin(admin.ModelAdmin):
    list_display = ("id", "patient", "visit_type", "visit_date", "created_at")
    list_filter = ("visit_type", "visit_date")
    search_fields = ("patient__first_name", "patient__last_name", "patient__phone")
    date_hierarchy = "visit_date"
    inlines = [VitalSignInline]


@admin.register(VitalSign)
class VitalSignAdmin(admin.ModelAdmin):
    list_display = ("id", "visit", "measured_at", "temperature_c", "bp_systolic", "bp_diastolic", "heart_rate_bpm")
    list_filter = ("measured_at",)
    search_fields = ("visit__patient__first_name", "visit__patient__last_name")