"""
Management command to send SMS appointment reminders.

Sends reminders for appointments scheduled for tomorrow (clinic-local date).
Designed to be run as a daily Render Cron Job.

Usage: python manage.py send_appointment_reminders
"""

import logging
from datetime import datetime, time, timedelta, timezone as dt_timezone
from zoneinfo import ZoneInfo

from django.conf import settings
from django.core.management.base import BaseCommand
from django.db.models import Q
from django.utils import timezone

from appointments.models import Appointment
from appointments.services.sms import send_sms

logger = logging.getLogger(__name__)

SMS_TEMPLATE = """Rappel de rendez-vous médical

Bonjour {prenom} {nom},
Vous avez un rendez-vous prévu demain ({date}) à {heure} avec le Dr Mukwamu B. Justin, Pédiatre.

Merci de bien vouloir arriver 10 minutes à l'avance.

Pour annuler ou reprogrammer votre rendez-vous, veuillez nous contacter au +243812345678.

Cordialement."""


class Command(BaseCommand):
    help = "Send SMS reminders for appointments scheduled for tomorrow"

    def handle(self, *args, **options):
        # Get clinic timezone (Render env: CLINIC_TIMEZONE=Africa/Kinshasa)
        tz_name = getattr(settings, "CLINIC_TIMEZONE", "Africa/Kinshasa")
        clinic_tz = ZoneInfo(tz_name)

        # Calculate "tomorrow" in clinic timezone
        now_clinic = timezone.now().astimezone(clinic_tz)
        tomorrow_date = now_clinic.date() + timedelta(days=1)

        self.stdout.write(f"Clinic timezone: {tz_name}")
        self.stdout.write(f"Clinic local time: {now_clinic.strftime('%Y-%m-%d %H:%M')}")
        self.stdout.write(f"Looking for appointments on: {tomorrow_date}")

        # Build tomorrow's boundaries in clinic timezone
        tomorrow_start_clinic = datetime.combine(tomorrow_date, time.min, tzinfo=clinic_tz)
        tomorrow_end_clinic = tomorrow_start_clinic + timedelta(days=1)

        # Convert to UTC for database query
        start_utc = tomorrow_start_clinic.astimezone(dt_timezone.utc)
        end_utc = tomorrow_end_clinic.astimezone(dt_timezone.utc)

        self.stdout.write(f"Query range (UTC): {start_utc} to {end_utc}")

        # Find appointments for tomorrow that haven't received a reminder
        # Only include appointments with reminders_enabled=True
        appointments = (
            Appointment.objects.filter(
                scheduled_at__gte=start_utc,
                scheduled_at__lt=end_utc,
                status__in=["SCHEDULED", "CONFIRMED"],
                reminders_enabled=True,
                reminder_sent_at__isnull=True,
            )
            .exclude(Q(patient__phone__isnull=True) | Q(patient__phone=""))
            .select_related("patient")
        )

        total = appointments.count()
        self.stdout.write(f"Found {total} appointment(s) to remind")

        if total == 0:
            self.stdout.write(self.style.SUCCESS("No reminders to send."))
            return

        sent_count = 0
        failed_count = 0

        for appointment in appointments:
            patient = appointment.patient
            phone = patient.phone.strip()

            # Format date and time in clinic timezone
            scheduled_local = appointment.scheduled_at.astimezone(clinic_tz)
            date_formatted = scheduled_local.strftime("%d/%m/%Y")
            time_formatted = scheduled_local.strftime("%H:%M")

            # Build SMS message
            message = SMS_TEMPLATE.format(
                prenom=patient.first_name,
                nom=patient.last_name,
                date=date_formatted,
                heure=time_formatted,
            )

            self.stdout.write(f"Sending reminder to {patient} at {phone}...")

            # Send SMS
            success = send_sms(phone, message)

            if success:
                # Mark reminder as sent
                appointment.reminder_sent_at = timezone.now()
                appointment.save(update_fields=["reminder_sent_at"])
                sent_count += 1
                self.stdout.write(self.style.SUCCESS(f"  Sent to {phone}"))
            else:
                failed_count += 1
                self.stdout.write(self.style.ERROR(f"  Failed for {phone}"))

        # Summary
        self.stdout.write("")
        self.stdout.write(f"Processed: {total}")
        self.stdout.write(self.style.SUCCESS(f"Sent: {sent_count}"))
        if failed_count > 0:
            self.stdout.write(self.style.ERROR(f"Failed: {failed_count}"))

        self.stdout.write(self.style.SUCCESS("Done."))
