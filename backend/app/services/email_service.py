import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import List, Optional, Dict
from app.config import settings
import logging

logger = logging.getLogger(__name__)


class EmailService:
    """
    Service for sending emails

    Supports:
    - Plain text and HTML emails
    - Multiple recipients
    - CC and BCC
    """

    def __init__(self):
        self.smtp_host = getattr(settings, "SMTP_HOST", "localhost")
        self.smtp_port = getattr(settings, "SMTP_PORT", 587)
        self.smtp_user = getattr(settings, "SMTP_USER", "")
        self.smtp_password = getattr(settings, "SMTP_PASSWORD", "")
        self.from_email = getattr(settings, "FROM_EMAIL", "noreply@hotelpms.com")
        self.from_name = getattr(settings, "FROM_NAME", "Assisi Social")

    def send_email(
        self,
        to_email: str,
        subject: str,
        body: str,
        html_body: Optional[str] = None,
        cc: Optional[List[str]] = None,
        bcc: Optional[List[str]] = None,
    ) -> bool:
        try:
            msg = MIMEMultipart("alternative")
            msg["Subject"] = subject
            msg["From"] = f"{self.from_name} <{self.from_email}>"
            msg["To"] = to_email.strip()

            if cc:
                msg["Cc"] = ", ".join(cc)

            # Plain text
            msg.attach(MIMEText(body, "plain"))

            # HTML
            if html_body:
                msg.attach(MIMEText(html_body, "html"))

            # Recipients
            recipients = [to_email.strip()]
            if cc:
                recipients.extend(cc)
            if bcc:
                recipients.extend(bcc)

            # Remove duplicates
            recipients = list(set(recipients))

            with smtplib.SMTP(self.smtp_host, self.smtp_port) as server:
                server.ehlo()

                # Use TLS only if not localhost
                if self.smtp_host != "localhost":
                    server.starttls()
                    server.ehlo()

                if self.smtp_user and self.smtp_password:
                    server.login(self.smtp_user, self.smtp_password)

                server.send_message(msg, self.from_email, recipients)

            logger.info(f"Email sent to {recipients}: {subject}")
            return True

        except Exception as e:
            logger.exception(f"Failed to send email to {to_email}")
            return False

    def send_bulk_email(
        self,
        recipients: List[str],
        subject: str,
        body: str,
        html_body: Optional[str] = None,
    ) -> Dict[str, object]:
        results = {
            "total": len(recipients),
            "sent": 0,
            "failed": 0,
            "failed_emails": [],
        }

        for email in recipients:
            success = self.send_email(email, subject, body, html_body)

            if success:
                results["sent"] += 1
            else:
                results["failed"] += 1
                results["failed_emails"].append(email)

        return results
