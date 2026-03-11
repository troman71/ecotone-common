"""Ecotone Common - Shared utilities for Ecotone Flask applications."""

__version__ = "0.1.0"

from .consent import get_current_eula_version, log_consent
from .email import LogBackend, SendGridBackend, SmtpBackend, create_email_backend
from .passwords import check_password, hash_password, validate_strength
from .tokens import TokenService

__all__ = [
    "hash_password",
    "check_password",
    "validate_strength",
    "TokenService",
    "SmtpBackend",
    "SendGridBackend",
    "LogBackend",
    "create_email_backend",
    "log_consent",
    "get_current_eula_version",
]
