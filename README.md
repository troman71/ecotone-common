# ecotone-common

Shared auth and utility primitives for Ecotone Python applications.

## Overview

Pure Python library (zero Flask dependency) providing four modules:

- **passwords** -- bcrypt hashing, legacy hash migration, and strength validation
- **tokens** -- signed, time-limited tokens via itsdangerous
- **email** -- pluggable backends (SMTP, SendGrid, log-only)
- **consent** -- EULA/consent audit logging

Requires Python 3.11+. Currently used by ecotone-impact.

## Installation

From git (private repo):

```bash
pip install git+https://github.com/troman71/ecotone-common.git@v0.1.0
```

Editable (local development):

```bash
pip install -e /path/to/ecotone-common
```

With SendGrid support:

```bash
pip install "ecotone-common[sendgrid] @ git+https://github.com/troman71/ecotone-common.git@v0.1.0"
```

Dependencies `bcrypt>=4.0` and `itsdangerous>=2.0` are installed automatically.

## Quick Start

```python
from ecotone_common import hash_password, check_password

hashed = hash_password("MySecurePass1")
assert check_password("MySecurePass1", hashed)
```

## Passwords

`ecotone_common.passwords`

```python
from ecotone_common import hash_password, check_password, needs_rehash, validate_strength

# Hash a password (returns UTF-8 bcrypt string)
hashed = hash_password("MySecurePass1")

# Verify against stored hash (supports bcrypt and legacy werkzeug hashes)
if check_password("MySecurePass1", hashed):
    print("Password correct")

# check_password auto-detects hash format:
#   $2b$... → bcrypt (current)
#   scrypt:... or pbkdf2:... → legacy werkzeug (auto-detected)

# Check if a hash needs upgrading to bcrypt
if needs_rehash(user['password_hash']):
    new_hash = hash_password(password)
    # UPDATE users SET password_hash = new_hash WHERE id = user_id

# Validate strength (returns list of failure messages, empty = valid)
failures = validate_strength("weak")
# ["Password must contain at least one uppercase letter",
#  "Password must contain at least one digit"]

# Custom rules
failures = validate_strength("abc", min_length=12, require_upper=False)
# ["Password must be at least 12 characters", "Password must contain at least one digit"]
```

**API:**

- `hash_password(password: str) -> str` -- always produces bcrypt
- `check_password(password: str, hashed: str) -> bool` -- bcrypt + legacy werkzeug (scrypt, pbkdf2)
- `needs_rehash(hashed: str) -> bool` -- True if hash is not bcrypt (should upgrade)
- `validate_strength(password: str, min_length=8, require_upper=True, require_lower=True, require_digit=True) -> list[str]`

## Tokens

`ecotone_common.tokens`

```python
from ecotone_common import TokenService

ts = TokenService(secret_key="your-app-secret-key")

# Email verification
token = ts.generate_verification_token("user@example.com")
email = ts.validate_verification_token(token, max_age=3600)  # returns email or None

# Password reset
token = ts.generate_reset_token("user@example.com")
email = ts.validate_reset_token(token, max_age=3600)  # returns email or None

# Admin approval (24h default expiry)
token = ts.generate_approval_token(user_id=42, action="approve")
data = ts.validate_approval_token(token, max_age=86400)  # returns {"user_id": "42", "action": "approve"} or None

# Generic tokens (custom salt and data)
token = ts.generate_token({"role": "admin", "org": 5}, salt="custom-purpose")
data = ts.validate_token(token, salt="custom-purpose", max_age=7200)  # returns dict or None

# Team invitations (random token, validated by DB lookup)
invite = TokenService.generate_invite_token()  # static method
is_valid = TokenService.validate_invite_token(invite)  # format check only
```

**API:**

- `TokenService(secret_key: str)`
- `generate_token(data: dict, salt: str) -> str`
- `validate_token(token: str, salt: str, max_age: int = 3600) -> dict | None`
- `generate_verification_token(email: str) -> str`
- `validate_verification_token(token: str, max_age: int = 3600) -> str | None`
- `generate_reset_token(email: str) -> str`
- `validate_reset_token(token: str, max_age: int = 3600) -> str | None`
- `generate_approval_token(user_id, action: str) -> str`
- `validate_approval_token(token: str, max_age: int = 86400) -> dict | None`
- `TokenService.generate_invite_token() -> str` (static)
- `TokenService.validate_invite_token(token: str) -> bool` (static)

## Email

`ecotone_common.email`

```python
from ecotone_common import create_email_backend

# Dev mode (no credentials needed)
backend = create_email_backend({})  # returns LogBackend
backend.send("user@example.com", "Welcome", "<h1>Hello</h1>")  # logs to console

# Production: SendGrid
backend = create_email_backend({
    "SENDGRID_API_KEY": "SG.xxxxx",
    "FROM_EMAIL": "noreply@ecotone-partners.com",
    "FROM_NAME": "Ecotone Impact",
})

# Production: SMTP (Gmail)
backend = create_email_backend({
    "SMTP_HOST": "smtp.gmail.com",
    "SMTP_PORT": 587,
    "SMTP_USERNAME": "user@gmail.com",
    "SMTP_PASSWORD": "app-password",
    "FROM_EMAIL": "user@gmail.com",
    "FROM_NAME": "Ecotone Impact",
})

# Send
success = backend.send(
    to="recipient@example.com",
    subject="Verify your email",
    html_body="<p>Click <a href='...'>here</a> to verify.</p>",
)
```

The factory checks config keys in order: `SENDGRID_API_KEY` -> `SendGridBackend`, `SMTP_HOST` -> `SmtpBackend`, otherwise -> `LogBackend`.

**API:**

- `create_email_backend(config: dict) -> EmailBackend`
- `backend.send(to: str, subject: str, html_body: str) -> bool`
- `SmtpBackend(host, port, username, password, from_email=None, from_name=None)`
- `SendGridBackend(api_key, from_email, from_name=None)`
- `LogBackend()`

**Config keys:** `SENDGRID_API_KEY`, `FROM_EMAIL`, `FROM_NAME`, `SMTP_HOST`, `SMTP_PORT`, `SMTP_USERNAME`, `SMTP_PASSWORD`

## Consent

`ecotone_common.consent`

```python
from ecotone_common import log_consent, get_current_eula_version

# Requires a psycopg2 cursor and consent_log / eula_versions tables in your DB

# Check current EULA version
version = get_current_eula_version(cursor)  # returns "1.0" or None

# Log user consent
log_consent(
    cursor,
    user_id=42,
    consent_type="eula",
    version="1.0",
    accepted=True,
    ip_address="192.168.1.1",
    user_agent="Mozilla/5.0...",
)
conn.commit()  # caller manages transactions
```

**API:**

- `log_consent(cursor, user_id, consent_type: str, version: str, accepted: bool, ip_address: str = None, user_agent: str = None)`
- `get_current_eula_version(cursor) -> str | None`

## Development

```bash
# Run tests
python -m pytest tests/

# Lint
ruff check src/ tests/

# Format
ruff format src/ tests/
```

## License

Private -- Ecotone Partners
