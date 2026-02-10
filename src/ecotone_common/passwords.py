"""Password hashing and strength validation using bcrypt."""

import bcrypt


def hash_password(password: str) -> str:
    """Hash a password using bcrypt. Returns UTF-8 string."""
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def check_password(password: str, hashed: str) -> bool:
    """Verify a password against a bcrypt hash."""
    return bcrypt.checkpw(password.encode("utf-8"), hashed.encode("utf-8"))


def validate_strength(
    password: str,
    min_length: int = 8,
    require_upper: bool = True,
    require_lower: bool = True,
    require_digit: bool = True,
) -> list[str]:
    """Validate password strength. Returns list of failure messages (empty if valid)."""
    failures = []

    if len(password) < min_length:
        failures.append(f"Password must be at least {min_length} characters")

    if require_upper and not any(c.isupper() for c in password):
        failures.append("Password must contain at least one uppercase letter")

    if require_lower and not any(c.islower() for c in password):
        failures.append("Password must contain at least one lowercase letter")

    if require_digit and not any(c.isdigit() for c in password):
        failures.append("Password must contain at least one digit")

    return failures
