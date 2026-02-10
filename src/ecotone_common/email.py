"""Email backends: SMTP, SendGrid, and log-only.

No Flask dependency. Caller provides configuration via constructor or factory.
"""

import logging
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

logger = logging.getLogger(__name__)


class EmailBackend:
    """Base email backend. Subclass and implement send()."""

    def send(self, to: str, subject: str, html_body: str) -> bool:
        """Send an email. Returns True on success."""
        raise NotImplementedError


class SmtpBackend(EmailBackend):
    """Send email via SMTP (e.g. Gmail)."""

    def __init__(
        self,
        host: str,
        port: int,
        username: str,
        password: str,
        from_email: str = None,
        from_name: str = None,
    ):
        self.host = host
        self.port = port
        self.username = username
        self.password = password
        self.from_email = from_email or username
        self.from_name = from_name

    def send(self, to: str, subject: str, html_body: str) -> bool:
        msg = MIMEMultipart("alternative")
        from_header = f"{self.from_name} <{self.from_email}>" if self.from_name else self.from_email
        msg["From"] = from_header
        msg["To"] = to
        msg["Subject"] = subject
        msg.attach(MIMEText(html_body, "html"))

        with smtplib.SMTP(self.host, self.port) as server:
            server.starttls()
            server.login(self.username, self.password)
            server.sendmail(self.from_email, to, msg.as_string())

        logger.info("SMTP email sent to %s: %s", to, subject)
        return True


class SendGridBackend(EmailBackend):
    """Send email via SendGrid API."""

    def __init__(self, api_key: str, from_email: str, from_name: str = None):
        self.api_key = api_key
        self.from_email = from_email
        self.from_name = from_name

    def send(self, to: str, subject: str, html_body: str) -> bool:
        import sendgrid
        from sendgrid.helpers.mail import Mail, Email, To, Content

        sg = sendgrid.SendGridAPIClient(api_key=self.api_key)

        from_addr = (
            Email(self.from_email, self.from_name) if self.from_name else Email(self.from_email)
        )
        message = Mail(
            from_email=from_addr,
            to_emails=To(to),
            subject=subject,
            html_content=Content("text/html", html_body),
        )

        response = sg.send(message)
        if response.status_code in (200, 201, 202):
            logger.info("SendGrid email sent to %s: %s", to, subject)
            return True

        logger.error("SendGrid error: %s", response.status_code)
        return False


class LogBackend(EmailBackend):
    """Dev mode: log email to console instead of sending."""

    def send(self, to: str, subject: str, html_body: str) -> bool:
        logger.info(
            "\n========== EMAIL (DEV MODE) ==========\n"
            "To: %s\nSubject: %s\nBody:\n%s\n"
            "======================================",
            to,
            subject,
            html_body,
        )
        return True


def create_email_backend(config: dict) -> EmailBackend:
    """Factory: create the appropriate backend from a config dict.

    Checks keys in order:
        - SENDGRID_API_KEY → SendGridBackend
        - SMTP_HOST → SmtpBackend
        - otherwise → LogBackend
    """
    if config.get("SENDGRID_API_KEY"):
        return SendGridBackend(
            api_key=config["SENDGRID_API_KEY"],
            from_email=config.get("FROM_EMAIL", "noreply@ecotone-partners.com"),
            from_name=config.get("FROM_NAME"),
        )

    if config.get("SMTP_HOST"):
        return SmtpBackend(
            host=config["SMTP_HOST"],
            port=int(config.get("SMTP_PORT", 587)),
            username=config.get("SMTP_USERNAME", ""),
            password=config.get("SMTP_PASSWORD", ""),
            from_email=config.get("FROM_EMAIL"),
            from_name=config.get("FROM_NAME"),
        )

    return LogBackend()
