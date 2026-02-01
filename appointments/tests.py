"""
Minimal tests for the SMS reminder system.

Covers:
- Phone number normalisation (DRC E.164)
- Phone masking for logs
- send_sms structured result on invalid phone (no SDK needed)
- Reminder query selects correct appointments (timezone-safe)
"""

from datetime import datetime, time, timedelta, timezone as dt_timezone
from unittest.mock import patch
from zoneinfo import ZoneInfo

from django.contrib.auth import get_user_model
from django.test import TestCase, override_settings
from django.utils import timezone

from appointments.models import Appointment
from appointments.services.sms import mask_phone, normalize_phone_drc, send_sms
from patients.models import Patient

User = get_user_model()


# =========================================================================
# Phone normalisation
# =========================================================================
class NormalizePhoneDRCTest(TestCase):
    """Test DRC phone number normalisation to E.164."""

    def test_local_with_leading_zero(self):
        self.assertEqual(normalize_phone_drc("0812345678"), "+243812345678")

    def test_local_without_leading_zero(self):
        self.assertEqual(normalize_phone_drc("812345678"), "+243812345678")

    def test_already_e164(self):
        self.assertEqual(normalize_phone_drc("+243812345678"), "+243812345678")

    def test_with_country_code_no_plus(self):
        self.assertEqual(normalize_phone_drc("243812345678"), "+243812345678")

    def test_with_spaces_and_dashes(self):
        self.assertEqual(normalize_phone_drc("+243 81-234-5678"), "+243812345678")

    def test_empty_string(self):
        self.assertIsNone(normalize_phone_drc(""))

    def test_none_input(self):
        self.assertIsNone(normalize_phone_drc(None))

    def test_too_short(self):
        self.assertIsNone(normalize_phone_drc("123"))

    def test_garbage_input(self):
        self.assertIsNone(normalize_phone_drc("abcdefg"))


# =========================================================================
# Phone masking
# =========================================================================
class MaskPhoneTest(TestCase):
    """Test phone number masking for safe logging."""

    def test_standard_mask(self):
        masked = mask_phone("+243812345678")
        self.assertNotIn("812345678", masked)
        self.assertTrue(masked.startswith("+2438"))
        self.assertTrue(masked.endswith("678"))

    def test_short_number_fully_masked(self):
        self.assertEqual(mask_phone("12345"), "***")

    def test_empty(self):
        self.assertEqual(mask_phone(""), "***")


# =========================================================================
# send_sms structured result on invalid phone
# =========================================================================
class SendSmsInvalidPhoneTest(TestCase):
    """send_sms should return ok=False without calling the provider for bad numbers."""

    def test_invalid_phone_returns_error(self):
        result = send_sms("invalid", "Hello")
        self.assertFalse(result["ok"])
        self.assertIsNotNone(result["error"])
        self.assertIsNone(result["message_id"])
        self.assertEqual(result["provider"], "africastalking")

    def test_empty_phone_returns_error(self):
        result = send_sms("", "Hello")
        self.assertFalse(result["ok"])
        self.assertIn("Invalid", result["error"])


# =========================================================================
# Reminder query logic
# =========================================================================
@override_settings(CLINIC_TIMEZONE="Africa/Kinshasa")
class ReminderQueryTest(TestCase):
    """Test that the reminder query selects the correct appointments."""

    @classmethod
    def setUpTestData(cls):
        cls.user = User.objects.create_user(username="testdoc", password="testpass123")
        cls.patient = Patient.objects.create(
            first_name="Jean",
            last_name="Dupont",
            sex="M",
            date_of_birth="2000-01-01",
            phone="+243812345678",
            address="Kinshasa",
            created_by=cls.user,
        )

    def _create_appointment(self, scheduled_at, **kwargs):
        defaults = {
            "patient": self.patient,
            "doctor": self.user,
            "scheduled_at": scheduled_at,
            "status": "SCHEDULED",
            "reminders_enabled": True,
        }
        defaults.update(kwargs)
        # Use objects.create to bypass clean() date validation for test fixtures
        return Appointment.objects.create(**defaults)

    def test_tomorrow_appointment_included(self):
        """An appointment scheduled for tomorrow should be found by the reminder query."""
        clinic_tz = ZoneInfo("Africa/Kinshasa")
        now_clinic = timezone.now().astimezone(clinic_tz)
        tomorrow = now_clinic.date() + timedelta(days=1)

        # Schedule at 10:00 tomorrow clinic time
        scheduled = datetime.combine(tomorrow, time(10, 0), tzinfo=clinic_tz)

        appt = self._create_appointment(scheduled_at=scheduled)

        # Reproduce the query from the management command
        tomorrow_start = datetime.combine(tomorrow, time.min, tzinfo=clinic_tz)
        tomorrow_end = tomorrow_start + timedelta(days=1)
        start_utc = tomorrow_start.astimezone(dt_timezone.utc)
        end_utc = tomorrow_end.astimezone(dt_timezone.utc)

        qs = Appointment.objects.filter(
            scheduled_at__gte=start_utc,
            scheduled_at__lt=end_utc,
            status__in=["SCHEDULED", "CONFIRMED"],
            reminders_enabled=True,
            reminder_sent_at__isnull=True,
        )
        self.assertIn(appt, qs)

    def test_already_sent_excluded(self):
        """Appointments with reminder_sent_at set should be excluded."""
        clinic_tz = ZoneInfo("Africa/Kinshasa")
        tomorrow = timezone.now().astimezone(clinic_tz).date() + timedelta(days=1)
        scheduled = datetime.combine(tomorrow, time(10, 0), tzinfo=clinic_tz)

        appt = self._create_appointment(
            scheduled_at=scheduled,
            reminder_sent_at=timezone.now(),
        )

        tomorrow_start = datetime.combine(tomorrow, time.min, tzinfo=clinic_tz)
        tomorrow_end = tomorrow_start + timedelta(days=1)
        start_utc = tomorrow_start.astimezone(dt_timezone.utc)
        end_utc = tomorrow_end.astimezone(dt_timezone.utc)

        qs = Appointment.objects.filter(
            scheduled_at__gte=start_utc,
            scheduled_at__lt=end_utc,
            status__in=["SCHEDULED", "CONFIRMED"],
            reminders_enabled=True,
            reminder_sent_at__isnull=True,
        )
        self.assertNotIn(appt, qs)

    def test_cancelled_excluded(self):
        """Cancelled appointments should not receive reminders."""
        clinic_tz = ZoneInfo("Africa/Kinshasa")
        tomorrow = timezone.now().astimezone(clinic_tz).date() + timedelta(days=1)
        scheduled = datetime.combine(tomorrow, time(10, 0), tzinfo=clinic_tz)

        appt = self._create_appointment(scheduled_at=scheduled, status="CANCELLED")

        tomorrow_start = datetime.combine(tomorrow, time.min, tzinfo=clinic_tz)
        tomorrow_end = tomorrow_start + timedelta(days=1)
        start_utc = tomorrow_start.astimezone(dt_timezone.utc)
        end_utc = tomorrow_end.astimezone(dt_timezone.utc)

        qs = Appointment.objects.filter(
            scheduled_at__gte=start_utc,
            scheduled_at__lt=end_utc,
            status__in=["SCHEDULED", "CONFIRMED"],
            reminders_enabled=True,
            reminder_sent_at__isnull=True,
        )
        self.assertNotIn(appt, qs)

    def test_reminders_disabled_excluded(self):
        """Appointments with reminders_enabled=False should be excluded."""
        clinic_tz = ZoneInfo("Africa/Kinshasa")
        tomorrow = timezone.now().astimezone(clinic_tz).date() + timedelta(days=1)
        scheduled = datetime.combine(tomorrow, time(10, 0), tzinfo=clinic_tz)

        appt = self._create_appointment(
            scheduled_at=scheduled,
            reminders_enabled=False,
        )

        tomorrow_start = datetime.combine(tomorrow, time.min, tzinfo=clinic_tz)
        tomorrow_end = tomorrow_start + timedelta(days=1)
        start_utc = tomorrow_start.astimezone(dt_timezone.utc)
        end_utc = tomorrow_end.astimezone(dt_timezone.utc)

        qs = Appointment.objects.filter(
            scheduled_at__gte=start_utc,
            scheduled_at__lt=end_utc,
            status__in=["SCHEDULED", "CONFIRMED"],
            reminders_enabled=True,
            reminder_sent_at__isnull=True,
        )
        self.assertNotIn(appt, qs)
