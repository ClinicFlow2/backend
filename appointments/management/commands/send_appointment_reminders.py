"""
Management command to send SMS appointment reminders.

Sends reminders for appointments scheduled for tomorrow (clinic-local date).
Designed to be run as a daily Render Cron Job.

Production hardening:
- Dynamic doctor name from appointment.doctor (fallback "votre médecin")
- Clinic phone from settings.CLINIC_PHONE
- Safety cap (SMS_MAX_REMINDERS_PER_RUN) to prevent mass accidental sends
- Records every send attempt in AppointmentSMSLog (success and failure)
- Masked phone numbers in console output
- select_related to avoid N+1 queries

Usage: python manage.py send_appointment_reminders
"""

import logging
from datetime import datetime, time, timedelta, timezone as dt_timezone
from zoneinfo import ZoneInfo

from django.conf import settings
from django.core.management.base import BaseCommand
from django.db.models import Q
from django.utils import timezone

from appointments.models import Appointment, AppointmentSMSLog
from appointments.services.sms import mask_phone, send_sms

logger = logging.getLogger(__name__)

SMS_TEMPLATE = """Rappel de rendez-vous médical

Bonjour {prenom} {nom},
Vous avez un rendez-vous prévu demain ({date}) à {heure} avec {docteur}.

Merci de bien vouloir arriver 10 minutes à l'avance.
{contact_line}
Cordialement."""


def _get_doctor_display(appointment):
    """Build a display name for the doctor assigned to this appointment."""
    doctor = appointment.doctor
    if not doctor:
        return "votre médecin"

    # Prefer display_name from profile (e.g. "Dr MUKWAMU B. Justin, Pédiatre")
    profile = getattr(doctor, "profile", None)
    if profile and getattr(profile, "display_name", ""):
        display = profile.display_name
        # Append specialization if not already in display_name
        spec = getattr(profile, "specialization", "")
        if spec and spec not in display:
            display = f"{display}, {spec}"
        return display

    # Fallback: build from user fields
    name = f"{doctor.last_name} {doctor.first_name}".strip() or doctor.username
    spec = ""
    if profile:
        spec = getattr(profile, "specialization", "") or "Médecin"
    return f"Dr {name}, {spec}" if spec else f"Dr {name}"


class Command(BaseCommand):
    help = "Send SMS reminders for appointments scheduled for tomorrow"

    def handle(self, *args, **options):
        # -----------------------------------------------------------
        # 1. Timezone setup
        # -----------------------------------------------------------
        tz_name = getattr(settings, "CLINIC_TIMEZONE", "Africa/Kinshasa")
        clinic_tz = ZoneInfo(tz_name)

        now_clinic = timezone.now().astimezone(clinic_tz)
        tomorrow_date = now_clinic.date() + timedelta(days=1)

        self.stdout.write(f"Clinic timezone: {tz_name}")
        self.stdout.write(f"Clinic local time: {now_clinic.strftime('%Y-%m-%d %H:%M')}")
        self.stdout.write(f"Looking for appointments on: {tomorrow_date}")

        # Tomorrow boundaries in clinic TZ -> converted to UTC for DB query
        tomorrow_start = datetime.combine(tomorrow_date, time.min, tzinfo=clinic_tz)
        tomorrow_end = tomorrow_start + timedelta(days=1)

        start_utc = tomorrow_start.astimezone(dt_timezone.utc)
        end_utc = tomorrow_end.astimezone(dt_timezone.utc)

        self.stdout.write(f"Query range (UTC): {start_utc} to {end_utc}")

        # -----------------------------------------------------------
        # 2. Query eligible appointments
        # -----------------------------------------------------------
        appointments = (
            Appointment.objects.filter(
                scheduled_at__gte=start_utc,
                scheduled_at__lt=end_utc,
                status__in=["SCHEDULED", "CONFIRMED"],
                reminders_enabled=True,
                reminder_sent_at__isnull=True,
            )
            .exclude(Q(patient__phone__isnull=True) | Q(patient__phone=""))
            .select_related("patient", "doctor", "doctor__profile")
        )

        total = appointments.count()
        self.stdout.write(f"Found {total} appointment(s) to remind")

        if total == 0:
            self.stdout.write(self.style.SUCCESS("No reminders to send."))
            return

        # -----------------------------------------------------------
        # 3. Safety cap
        # -----------------------------------------------------------
        max_cap = getattr(settings, "SMS_MAX_REMINDERS_PER_RUN", 200)
        if total > max_cap:
            msg = (
                f"SAFETY CAP: {total} reminders exceed limit of {max_cap}. "
                f"Aborting to prevent mass sends. "
                f"Raise SMS_MAX_REMINDERS_PER_RUN env var if this is intentional."
            )
            self.stdout.write(self.style.ERROR(msg))
            logger.critical(msg)
            return

        # -----------------------------------------------------------
        # 4. Clinic contact line
        # -----------------------------------------------------------
        clinic_phone = getattr(settings, "CLINIC_PHONE", "")
        if clinic_phone:
            contact_line = (
                f"\nPour annuler ou reprogrammer, contactez-nous au {clinic_phone}."
            )
        else:
            contact_line = ""

        # -----------------------------------------------------------
        # 5. Send loop
        # -----------------------------------------------------------
        sent_count = 0
        failed_count = 0

        for appointment in appointments:
            patient = appointment.patient
            phone_raw = patient.phone.strip()

            # Format date/time in clinic timezone
            scheduled_local = appointment.scheduled_at.astimezone(clinic_tz)
            date_fmt = scheduled_local.strftime("%d/%m/%Y")
            time_fmt = scheduled_local.strftime("%H:%M")

            doctor_display = _get_doctor_display(appointment)

            message = SMS_TEMPLATE.format(
                prenom=patient.first_name,
                nom=patient.last_name,
                date=date_fmt,
                heure=time_fmt,
                docteur=doctor_display,
                contact_line=contact_line,
            )

            masked = mask_phone(phone_raw)
            self.stdout.write(f"Sending reminder to {patient} at {masked}...")

            # --- Call hardened SMS service ---
            result = send_sms(phone_raw, message)

            # --- Record in DB ---
            AppointmentSMSLog.objects.create(
                appointment=appointment,
                phone=result.get("phone_normalised") or phone_raw,
                provider=result.get("provider", "africastalking"),
                status="SUCCESS" if result["ok"] else "FAILED",
                message_id=result.get("message_id") or "",
                error_message=result.get("error") or "",
            )

            if result["ok"]:
                appointment.reminder_sent_at = timezone.now()
                appointment.save(update_fields=["reminder_sent_at"])
                sent_count += 1
                self.stdout.write(self.style.SUCCESS(f"  Sent to {masked}"))
            else:
                failed_count += 1
                err = result.get("error", "unknown")
                self.stdout.write(self.style.ERROR(f"  Failed for {masked}: {err}"))

        # -----------------------------------------------------------
        # 6. Summary
        # -----------------------------------------------------------
        self.stdout.write("")
        self.stdout.write(f"Processed: {total}")
        self.stdout.write(self.style.SUCCESS(f"Sent: {sent_count}"))
        if failed_count > 0:
            self.stdout.write(self.style.ERROR(f"Failed: {failed_count}"))

        logger.info(
            "SMS reminder run complete: total=%d sent=%d failed=%d",
            total, sent_count, failed_count,
        )
        self.stdout.write(self.style.SUCCESS("Done."))
