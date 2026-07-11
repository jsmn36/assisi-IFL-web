"""Email service stub"""
import logging

logger = logging.getLogger(__name__)


class EmailService:
    async def send_email(self, to: str, subject: str, body: str, **kwargs):
        logger.info(f"[STUB] Email to {to}: {subject}")
        return {"status": "stub", "to": to, "subject": subject}


email_service = EmailService()
