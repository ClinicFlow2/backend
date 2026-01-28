"""
SMS sending service using Africa's Talking.
"""

import logging
from django.conf import settings

logger = logging.getLogger(__name__)


def send_sms(phone_number: str, message: str) -> bool:
    """
    Send an SMS via Africa's Talking.

    Args:
        phone_number: Recipient phone number (international format recommended)
        message: SMS message content

    Returns:
        True if SMS was sent successfully, False otherwise
    """
    username = settings.AFRICASTALKING_USERNAME
    api_key = settings.AFRICASTALKING_API_KEY
    sender_id = settings.AFRICASTALKING_SENDER_ID

    if not username or not api_key:
        logger.error("Africa's Talking credentials not configured")
        return False

    try:
        import africastalking

        africastalking.initialize(username, api_key)
        sms = africastalking.SMS

        # Build kwargs for send
        kwargs = {
            "message": message,
            "recipients": [phone_number],
        }
        if sender_id:
            kwargs["sender_id"] = sender_id

        response = sms.send(**kwargs)

        # Africa's Talking returns: {"SMSMessageData": {"Recipients": [{"status": "Success", ...}]}}

        recipients = response.get("SMSMessageData", {}).get("Recipients", [])
        if recipients and recipients[0].get("status") == "Success":
            logger.info(f"SMS sent successfully to {phone_number}")
            return True

        status = recipients[0].get("status") if recipients else "Unknown"
        logger.warning(f"SMS send failed for {phone_number}: {status}")
        return False

    except Exception as e:
        logger.error(f"SMS send error for {phone_number}: {e}")
        return False
