"""Token generation and validation using itsdangerous.

Wraps URLSafeTimedSerializer for signed, time-limited tokens.
No Flask dependency — caller provides the secret key.
"""

import logging
import secrets
from itsdangerous import URLSafeTimedSerializer, SignatureExpired, BadSignature

logger = logging.getLogger(__name__)


class TokenService:
    """Token generation and validation for auth workflows."""

    def __init__(self, secret_key: str):
        self._serializer = URLSafeTimedSerializer(secret_key)

    # --- Generic ---

    def generate_token(self, data: dict, salt: str) -> str:
        """Generate a signed token with arbitrary data."""
        return self._serializer.dumps(data, salt=salt)

    def validate_token(self, token: str, salt: str, max_age: int = 3600) -> dict | None:
        """Validate a signed token. Returns data or None."""
        try:
            return self._serializer.loads(token, salt=salt, max_age=max_age)
        except SignatureExpired:
            logger.warning("Token expired (salt=%s)", salt)
            return None
        except BadSignature:
            logger.warning("Invalid token (salt=%s)", salt)
            return None

    # --- Email Verification ---

    def generate_verification_token(self, email: str) -> str:
        """Generate email verification token (1 hour expiry enforced on validation)."""
        return self._serializer.dumps(email, salt="email-verify")

    def validate_verification_token(self, token: str, max_age: int = 3600) -> str | None:
        """Validate email verification token. Returns email or None."""
        try:
            return self._serializer.loads(token, salt="email-verify", max_age=max_age)
        except SignatureExpired:
            logger.warning("Verification token expired")
            return None
        except BadSignature:
            logger.warning("Invalid verification token")
            return None

    # --- Password Reset ---

    def generate_reset_token(self, email: str) -> str:
        """Generate password reset token (1 hour expiry enforced on validation)."""
        return self._serializer.dumps(email, salt="password-reset")

    def validate_reset_token(self, token: str, max_age: int = 3600) -> str | None:
        """Validate password reset token. Returns email or None."""
        try:
            return self._serializer.loads(token, salt="password-reset", max_age=max_age)
        except SignatureExpired:
            logger.warning("Reset token expired")
            return None
        except BadSignature:
            logger.warning("Invalid reset token")
            return None

    # --- Approval Actions ---

    def generate_approval_token(self, user_id, action: str) -> str:
        """Generate approval/rejection token for admin (24 hour expiry)."""
        return self._serializer.dumps(
            {"user_id": str(user_id), "action": action}, salt="approval-action"
        )

    def validate_approval_token(self, token: str, max_age: int = 86400) -> dict | None:
        """Validate approval token. Returns dict with user_id and action, or None."""
        try:
            return self._serializer.loads(token, salt="approval-action", max_age=max_age)
        except SignatureExpired:
            logger.warning("Approval token expired")
            return None
        except BadSignature:
            logger.warning("Invalid approval token")
            return None

    # --- Team Invitations ---

    @staticmethod
    def generate_invite_token() -> str:
        """Generate a secure random invite token (validated by DB lookup, not signature)."""
        return secrets.token_urlsafe(32)

    @staticmethod
    def validate_invite_token(token: str) -> bool:
        """Check invite token format. Actual validation is by database lookup."""
        return token is not None and len(token) > 0
