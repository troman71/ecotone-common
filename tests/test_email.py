"""Tests for ecotone_common.email."""

import logging
from unittest.mock import MagicMock, patch

from ecotone_common.email import LogBackend, SendGridBackend, SmtpBackend, create_email_backend


def test_log_backend(caplog):
    backend = LogBackend()
    with caplog.at_level(logging.INFO):
        result = backend.send("test@example.com", "Hello", "<b>Hi</b>")
    assert result is True
    assert "test@example.com" in caplog.text
    assert "Hello" in caplog.text


def test_smtp_backend_sends():
    backend = SmtpBackend(
        host="smtp.test.com",
        port=587,
        username="user",
        password="pass",
        from_name="Test App",
    )
    with patch("ecotone_common.email.smtplib.SMTP") as mock_smtp:
        ctx = MagicMock()
        mock_smtp.return_value.__enter__ = MagicMock(return_value=ctx)
        mock_smtp.return_value.__exit__ = MagicMock(return_value=False)

        result = backend.send("to@example.com", "Subject", "<p>Body</p>")

    assert result is True
    ctx.starttls.assert_called_once()
    ctx.login.assert_called_once_with("user", "pass")
    ctx.sendmail.assert_called_once()
    args = ctx.sendmail.call_args[0]
    assert args[0] == "user"  # from
    assert args[1] == "to@example.com"  # to


def test_smtp_backend_custom_from():
    backend = SmtpBackend(
        host="smtp.test.com",
        port=587,
        username="user",
        password="pass",
        from_email="custom@example.com",
        from_name="Custom Name",
    )
    with patch("ecotone_common.email.smtplib.SMTP") as mock_smtp:
        ctx = MagicMock()
        mock_smtp.return_value.__enter__ = MagicMock(return_value=ctx)
        mock_smtp.return_value.__exit__ = MagicMock(return_value=False)

        backend.send("to@example.com", "Test", "<p>Test</p>")

    args = ctx.sendmail.call_args[0]
    assert args[0] == "custom@example.com"


def test_create_email_backend_sendgrid():
    backend = create_email_backend({"SENDGRID_API_KEY": "sg-key", "FROM_EMAIL": "a@b.com"})
    assert isinstance(backend, SendGridBackend)
    assert backend.api_key == "sg-key"


def test_create_email_backend_smtp():
    backend = create_email_backend(
        {
            "SMTP_HOST": "smtp.gmail.com",
            "SMTP_PORT": "587",
            "SMTP_USERNAME": "user",
            "SMTP_PASSWORD": "pass",
        }
    )
    assert isinstance(backend, SmtpBackend)
    assert backend.host == "smtp.gmail.com"


def test_create_email_backend_log_fallback():
    backend = create_email_backend({})
    assert isinstance(backend, LogBackend)
