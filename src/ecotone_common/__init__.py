"""Ecotone Common - Shared utilities for Ecotone Flask applications."""

__version__ = "0.1.0"

from .passwords import hash_password, check_password, validate_strength
from .tokens import TokenService
from .email import SmtpBackend, SendGridBackend, LogBackend, create_email_backend
from .consent import log_consent, get_current_eula_version

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
