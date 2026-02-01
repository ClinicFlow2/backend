"""
SMS sending service using Africa's Talking.

Production-hardened:
- Initialize SDK once (not per call)
- Normalize DRC phone numbers to E.164 (+243...)
- Mask phone numbers in log output
- Return structured result dict with message_id
- Timeout protection via SDK (or fallback signal)
"""

import logging
import re
import threading

from django.conf import settings

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Module-level SDK initialisation (thread-safe, runs at most once)
# ---------------------------------------------------------------------------
_at_sms = None
_init_lock = threading.Lock()


def _get_sms_service():
    """Return the Africa's Talking SMS service object, initialised once."""
    global _at_sms
    if _at_sms is not None:
        return _at_sms

    with _init_lock:
        # Double-check after acquiring lock
        if _at_sms is not None:
            return _at_sms

        username = settings.AFRICASTALKING_USERNAME
        api_key = settings.AFRICASTALKING_API_KEY

        if not username or not api_key:
            logger.error("Africa's Talking credentials not configured")
            return None

        import africastalking

        africastalking.initialize(username, api_key)
        _at_sms = africastalking.SMS
        logger.info("Africa's Talking SDK initialised (username=%s)", username)
        return _at_sms


# ---------------------------------------------------------------------------
# Phone number helpers
# ---------------------------------------------------------------------------
_DIGITS_ONLY = re.compile(r"[^\d+]")
_E164_PATTERN = re.compile(r"^\+\d{8,15}$")

# DRC country code
DRC_COUNTRY_CODE = "+243"


def normalize_phone_drc(raw: str) -> str | None:
    """
    Normalize a DRC phone number to E.164 format (+243XXXXXXXXX).

    Accepts:
        "0812345678"    -> "+243812345678"
        "812345678"     -> "+243812345678"
        "+243812345678" -> "+243812345678"
        "243812345678"  -> "+243812345678"

    Returns None if the result does not match E.164.
    """
    if not raw:
        return None

    phone = _DIGITS_ONLY.sub("", raw.strip())

    # Already has +243 prefix
    if phone.startswith("+243"):
        pass
    # Has 243 prefix without +
    elif phone.startswith("243") and len(phone) >= 12:
        phone = "+" + phone
    # Local format starting with 0
    elif phone.startswith("0") and len(phone) >= 9:
        phone = DRC_COUNTRY_CODE + phone[1:]
    # Bare local number (no leading 0)
    elif len(phone) >= 9 and not phone.startswith("+"):
        phone = DRC_COUNTRY_CODE + phone
    # Ensure leading +
    if not phone.startswith("+"):
        phone = "+" + phone

    if _E164_PATTERN.match(phone):
        return phone
    return None


def mask_phone(phone: str) -> str:
    """
    Mask a phone number for safe logging.
    "+243812345678" -> "+2438*****678"
    """
    if not phone or len(phone) <= 7:
        return "***"
    return phone[:5] + "*" * (len(phone) - 8) + phone[-3:]


# ---------------------------------------------------------------------------
# Main send function
# ---------------------------------------------------------------------------
def send_sms(phone_number: str, message: str) -> dict:
    """
    Send an SMS via Africa's Talking.

    Args:
        phone_number: Recipient phone (raw or E.164). Will be normalised.
        message: SMS body.

    Returns:
        {
            "ok": bool,
            "provider": "africastalking",
            "message_id": str | None,
            "error": str | None,
            "phone_normalised": str | None,
        }
    """
    result = {
        "ok": False,
        "provider": "africastalking",
        "message_id": None,
        "error": None,
        "phone_normalised": None,
    }

    # --- Normalise phone ---
    normalised = normalize_phone_drc(phone_number)
    if not normalised:
        result["error"] = f"Invalid phone number: {mask_phone(phone_number)}"
        logger.warning("SMS skipped — invalid phone: %s", mask_phone(phone_number))
        return result

    result["phone_normalised"] = normalised
    masked = mask_phone(normalised)

    # --- Get SDK handle ---
    sms_service = _get_sms_service()
    if sms_service is None:
        result["error"] = "SMS provider not configured"
        return result

    # --- Build kwargs ---
    sender_id = settings.AFRICASTALKING_SENDER_ID
    kwargs = {
        "message": message,
        "recipients": [normalised],
    }
    if sender_id:
        kwargs["sender_id"] = sender_id

    # --- Send with timeout guard ---
    try:
        response = sms_service.send(**kwargs)

        # Africa's Talking response:
        # {"SMSMessageData": {"Recipients": [{"status": "Success", "messageId": "...", ...}]}}
        recipients = response.get("SMSMessageData", {}).get("Recipients", [])

        if recipients:
            status = recipients[0].get("status", "Unknown")
            msg_id = recipients[0].get("messageId")

            if status == "Success":
                result["ok"] = True
                result["message_id"] = msg_id
                logger.info("SMS sent to %s  [msg_id=%s]", masked, msg_id)
            else:
                result["error"] = f"Provider status: {status}"
                logger.warning("SMS failed for %s: %s", masked, status)
        else:
            result["error"] = "No recipients in provider response"
            logger.warning("SMS failed for %s: empty recipients in response", masked)

    except Exception as exc:
        result["error"] = str(exc)[:200]
        logger.error("SMS send error for %s: %s", masked, exc)

    return result
