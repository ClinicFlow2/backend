from django.contrib import admin, messages
from django.utils import timezone

from .models import Appointment
from visits.models import Visit


@admin.action(description="Mark selected appointments as CONFIRMED")
def mark_confirmed(modeladmin, request, queryset):
    updated = queryset.update(status="CONFIRMED")
    modeladmin.message_user(
        request,
        f"{updated} appointment(s) marked CONFIRMED.",
        level=messages.SUCCESS,
    )


@admin.action(description="Mark selected appointments as CANCELLED")
def mark_cancelled(modeladmin, request, queryset):
    updated = queryset.update(status="CANCELLED")
    modeladmin.message_user(
        request,
        f"{updated} appointment(s) marked CANCELLED.",
        level=messages.SUCCESS,
    )


@admin.action(description="Mark selected appointments as NO_SHOW")
def mark_no_show(modeladmin, request, queryset):
    updated = queryset.update(status="NO_SHOW")
    modeladmin.message_user(
        request,
        f"{updated} appointment(s) marked NO_SHOW.",
        level=messages.SUCCESS,
    )


@admin.action(description="Mark selected appointments as COMPLETED")
def mark_completed(modeladmin, request, queryset):
    updated = queryset.update(status="COMPLETED")
    modeladmin.message_user(
        request,
        f"{updated} appointment(s) marked COMPLETED.",
        level=messages.SUCCESS,
    )


@admin.action(description="Create Visit + link to Appointment (only if missing)")
def create_visit_from_appointment(modeladmin, request, queryset):
    created = 0
    skipped = 0
    failed = 0

    # select_related avoids extra DB queries
    for appt in queryset.select_related("patient", "visit"):
        if appt.visit_id:
            skipped += 1
            continue

        try:
            visit = Visit.objects.create(
                patient=appt.patient,
                # your Visit model uses visit_date (DateTimeField)
                visit_date=appt.scheduled_at or timezone.now(),
                visit_type="CONSULTATION",
                chief_complaint=appt.reason or "",
            )

            # link appointment -> visit (OneToOne)
            appt.visit = visit

            # optional: once a visit exists, this appointment is completed
            appt.status = "COMPLETED"

            # IMPORTANT: avoid full_clean blocking due to "past date" rule for SCHEDULED/CONFIRMED
            appt.save(update_fields=["visit", "status"])

            created += 1

        except Exception as e:
            failed += 1
            modeladmin.message_user(
                request,
                f"Appointment #{appt.id} failed: {e}",
                level=messages.ERROR,
            )

    if created:
        modeladmin.message_user(
            request,
            f"Created {created} visit(s) and linked them.",
            level=messages.SUCCESS,
        )
    if skipped:
        modeladmin.message_user(
            request,
            f"Skipped {skipped} appointment(s) (visit already exists).",
            level=messages.WARNING,
        )
    if failed and not created:
        modeladmin.message_user(
            request,
            "No visits were created. See errors above.",
            level=messages.ERROR,
        )


@admin.register(Appointment)
class AppointmentAdmin(admin.ModelAdmin):
    list_display = ("id", "patient", "scheduled_at", "status", "visit")
    list_filter = ("status", "scheduled_at")
    search_fields = ("patient__first_name", "patient__last_name", "reason")
    autocomplete_fields = ("patient", "visit")
    ordering = ("-scheduled_at",)

    actions = [
        mark_confirmed,
        mark_cancelled,
        mark_no_show,
        mark_completed,
        create_visit_from_appointment,
    ]