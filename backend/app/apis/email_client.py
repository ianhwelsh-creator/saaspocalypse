"""Email delivery via Resend API."""

import logging

import resend

logger = logging.getLogger(__name__)


class EmailClient:
    def __init__(self, api_key: str):
        self._api_key = api_key
        if api_key:
            resend.api_key = api_key

    async def send_email(self, to: str, subject: str, html: str) -> dict:
        """Send an email via Resend."""
        if not self._api_key:
            raise ValueError("Resend API key not configured")

        try:
            params = {
                "from": "SaaSpocalypse <newsletter@saaspocalypse.com>",
                "to": [to],
                "subject": subject,
                "html": html,
            }
            email = resend.Emails.send(params)
            logger.info(f"Email sent to {to}: {email.get('id', 'unknown')}")
            return {"success": True, "id": email.get("id")}
        except Exception as e:
            logger.error(f"Email send failed: {e}")
            raise
