# Coding Conventions

**Analysis Date:** 2026-02-10

## Naming Patterns

**Files:**
- Lowercase with underscores: `passwords.py`, `tokens.py`, `email.py`, `consent.py`
- Test files use `test_` prefix: `test_passwords.py`, `test_tokens.py`

**Functions:**
- Lowercase with underscores: `hash_password()`, `check_password()`, `validate_strength()`
- Action verbs lead: `generate_*`, `validate_*`, `check_*`, `log_*`, `create_*`

**Variables:**
- Lowercase with underscores: `hashed`, `from_email`, `user_id`, `max_age`
- Private attributes use single underscore prefix: `_serializer`, `_salt`

**Types:**
- Classes use PascalCase: `TokenService`, `SmtpBackend`, `SendGridBackend`, `LogBackend`, `EmailBackend`
- Type hints use modern syntax: `str`, `bool`, `int`, `dict | None`, `list[str]`

**Constants:**
- Config keys are uppercase: `SENDGRID_API_KEY`, `SMTP_HOST`, `FROM_EMAIL`

## Code Style

**Formatting:**
- No explicit linter config detected (no `.flake8`, `.pylintrc`, `ruff.toml`)
- Code follows PEP 8 conventions implicitly through manual adherence
- Import organization is clean and alphabetical where applicable
- No trailing whitespace observed

**Linting:**
- No automated linting tool configured in `pyproject.toml`
- Code conventions enforced through manual review and testing

**Indentation:**
- 4 spaces consistently used throughout codebase

## Import Organization

**Order:**
1. Standard library: `logging`, `smtplib`, `email.mime.*`, `secrets`, `time`
2. Third-party: `bcrypt`, `itsdangerous`, `sendgrid`
3. Relative imports: `.passwords`, `.tokens`, `.email`, `.consent`

**Pattern:**
- Imports grouped by category with blank line between groups
- All imports at module level
- Conditional imports used where optional dependencies required (e.g., `sendgrid` in `SendGridBackend.send()`)

**Path Aliases:**
- None detected; relative imports from `ecotone_common` package used directly

## Error Handling

**Patterns:**
- Exceptions caught and logged with context: `SignatureExpired`, `BadSignature` from `itsdangerous`
- Logging used to record exceptions: `logger.warning("Token expired (salt=%s)", salt)`
- Functions return `None` on error rather than raising: `validate_token()`, `validate_verification_token()`, `validate_reset_token()`, `validate_approval_token()`
- Return type is explicit: `dict | None`, `str | None`, `bool`

**Location:** `src/ecotone_common/tokens.py:26-35` shows standard pattern

```python
def validate_token(self, token: str, salt: str, max_age: int = 3600) -> dict | None:
    try:
        return self._serializer.loads(token, salt=salt, max_age=max_age)
    except SignatureExpired:
        logger.warning("Token expired (salt=%s)", salt)
        return None
    except BadSignature:
        logger.warning("Invalid token (salt=%s)", salt)
        return None
```

## Logging

**Framework:** Python standard `logging` module

**Initialization:** Each module creates module-level logger:
```python
logger = logging.getLogger(__name__)
```

**Patterns:**
- `logger.info()` for successful operations: `logger.info("SMTP email sent to %s: %s", to, subject)`
- `logger.warning()` for handled exceptions: `logger.warning("Token expired (salt=%s)", salt)`
- `logger.error()` for failures: `logger.error("SendGrid error: %s", response.status_code)`
- String interpolation via format args, not f-strings: `logger.info("SMTP email sent to %s: %s", to, subject)`

**Location:**
- `src/ecotone_common/tokens.py:11` - Logger initialization
- `src/ecotone_common/email.py:11` - Logger initialization

## Comments

**When to Comment:**
- Function docstrings (triple-quoted) always included
- Docstrings describe purpose, parameters, return values
- Inline comments minimal; code is self-documenting through clear naming

**JSDoc/TSDoc:**
- Not applicable; Python project uses docstrings exclusively

**Docstring Pattern:**
```python
def hash_password(password: str) -> str:
    """Hash a password using bcrypt. Returns UTF-8 string."""
```

## Function Design

**Size:** Functions are small and single-purpose (5-25 lines)

**Parameters:**
- Required parameters first, optional with defaults after
- Type hints on all parameters and return values
- Defaults provided for email config: `from_email=None`, `from_name=None`

**Return Values:**
- Boolean for validation/check operations: `check_password()` → `bool`
- None for optional results: `validate_token()` → `dict | None`
- String for generation: `generate_token()` → `str`
- Implicit None for side effects: `log_consent()` performs insert, returns nothing

**Example from `src/ecotone_common/passwords.py:22-28`:**
```python
def validate_strength(
    password: str,
    min_length: int = 8,
    require_upper: bool = True,
    require_lower: bool = True,
    require_digit: bool = True,
) -> list[str]:
    """Validate password strength. Returns list of failure messages (empty if valid)."""
```

## Module Design

**Exports:**
- Selective exports via `__init__.py`: `from .passwords import hash_password, check_password, validate_strength`
- Only public APIs exported; internal helpers stay in their modules
- Module-level logger is internal (not exported)

**Barrel Files:**
- `src/ecotone_common/__init__.py` serves as barrel file
- Collects all public APIs in one place for clean imports
- Includes version number: `__version__ = "0.1.0"`

**Module Purpose Pattern:**
- Each module has single responsibility:
  - `passwords.py` - Password hashing and validation
  - `tokens.py` - Token generation and validation
  - `email.py` - Email sending backends
  - `consent.py` - Consent logging helpers
- No circular dependencies observed
- Minimal coupling between modules

## Class Design

**Structure:**
- Base classes define interface: `EmailBackend` with abstract `send()` method
- Subclasses implement backends: `SmtpBackend`, `SendGridBackend`, `LogBackend`
- Service class wraps third-party library: `TokenService` wraps `URLSafeTimedSerializer`

**Encapsulation:**
- Private attributes prefixed with underscore: `self._serializer`
- Configuration passed via constructor; immutable after initialization
- No class variables; all state instance-based

**Example from `src/ecotone_common/tokens.py:14-24`:**
```python
class TokenService:
    """Token generation and validation for auth workflows."""

    def __init__(self, secret_key: str):
        self._serializer = URLSafeTimedSerializer(secret_key)

    def generate_token(self, data: dict, salt: str) -> str:
        """Generate a signed token with arbitrary data."""
        return self._serializer.dumps(data, salt=salt)
```

## No Flask Dependency

**Important:** All modules are framework-agnostic. They do not import Flask or depend on Flask context.

- `tokens.py`: "No Flask dependency — caller provides the secret key"
- `email.py`: "No Flask dependency. Caller provides configuration via constructor or factory"
- `consent.py`: "No Flask dependency. Caller provides a DB cursor"
- `passwords.py`: Pure cryptographic functions, no framework dependency

This allows these utilities to be used in multiple Flask apps, batch scripts, or other Python environments without coupling to Flask.

---

*Convention analysis: 2026-02-10*
