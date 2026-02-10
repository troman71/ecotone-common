# Codebase Structure

**Analysis Date:** 2026-02-10

## Directory Layout

```
ecotone-common/
├── pyproject.toml          # Package manifest (name, version, dependencies)
├── .gitignore              # Standard Python ignores
├── src/
│   └── ecotone_common/     # Main package (pip installable)
│       ├── __init__.py     # Public API exports
│       ├── passwords.py    # Password hashing and strength validation
│       ├── tokens.py       # Signed token generation and validation
│       ├── email.py        # SMTP, SendGrid, and log email backends
│       └── consent.py      # Consent logging and EULA version queries
└── tests/
    ├── test_passwords.py   # Password hashing and validation tests
    ├── test_tokens.py      # Token generation and validation tests
    ├── test_email.py       # Email backend tests
    └── test_consent.py     # Consent logging and EULA tests
```

## Directory Purposes

**`src/ecotone_common/`:**
- Purpose: Main package code (what gets installed via pip)
- Contains: Pure Python modules implementing auth/consent utilities
- Key files: `__init__.py` (exports), `tokens.py` (largest/most complex)

**`tests/`:**
- Purpose: pytest test suite
- Contains: Unit tests for each module, mocking external services
- Key files: `test_tokens.py` (comprehensive token workflows), `test_email.py` (backend mocking)

## Key File Locations

**Entry Points (public API):**
- `src/ecotone_common/__init__.py`: Main package exports
  - Imports and re-exports: `hash_password`, `check_password`, `validate_strength`, `TokenService`, `SmtpBackend`, `SendGridBackend`, `LogBackend`, `create_email_backend`, `log_consent`, `get_current_eula_version`
  - Version string: `__version__ = "0.1.0"`

**Core Modules:**
- `src/ecotone_common/passwords.py`: Password hashing (bcrypt) and strength validation
- `src/ecotone_common/tokens.py`: TokenService class for signed, time-limited tokens (email verification, password reset, approvals, invites)
- `src/ecotone_common/email.py`: EmailBackend abstraction with SendGrid, SMTP, and logging implementations
- `src/ecotone_common/consent.py`: Consent logging and EULA version queries (thin database wrappers)

**Configuration:**
- `pyproject.toml`: Package name, version 0.1.0, Python >=3.11, core dependencies (bcrypt, itsdangerous), optional sendgrid

**Testing:**
- `tests/test_passwords.py`: Hash roundtrip, strength validation with custom rules
- `tests/test_tokens.py`: All token types (verification, reset, approval, generic, invites), expiry, signature failure
- `tests/test_email.py`: LogBackend, SmtpBackend with mocked SMTP, SendGridBackend instantiation, factory selection
- `tests/test_consent.py`: Consent logging with optional fields, EULA version queries with dict and tuple cursors

## Naming Conventions

**Files:**
- Module files are lowercase with underscores: `passwords.py`, `tokens.py`, `email.py`, `consent.py`
- Test files follow pytest convention: `test_<module>.py` (e.g., `test_passwords.py`)
- Main package directory is lowercase with underscore: `ecotone_common`

**Functions:**
- Snake_case, descriptive: `hash_password()`, `check_password()`, `validate_strength()`, `log_consent()`, `get_current_eula_version()`, `create_email_backend()`
- Factory functions prefixed with `create_`: `create_email_backend()`
- Specialized token methods use `generate_*` and `validate_*`: `generate_verification_token()`, `validate_verification_token()`, etc.

**Classes:**
- PascalCase: `TokenService`, `EmailBackend`, `SmtpBackend`, `SendGridBackend`, `LogBackend`
- Backends inherit from `EmailBackend` base class
- No generic naming; each class is explicit about its purpose

**Variables:**
- Snake_case for local variables: `secret_key`, `from_email`, `max_age`, `html_body`
- Configuration dicts use SCREAMING_SNAKE_CASE keys: `SENDGRID_API_KEY`, `SMTP_HOST`, `SMTP_PORT`, `SMTP_USERNAME`, `SMTP_PASSWORD`, `FROM_EMAIL`, `FROM_NAME`

**Type Hints:**
- Modern Python 3.10+ syntax: `str | None` instead of `Optional[str]`, `list[str]` instead of `List[str]`, `dict` not `Dict`
- Used throughout public functions and class methods

## Where to Add New Code

**New Authentication Feature:**
- Primary code: `src/ecotone_common/<feature>.py` (new module if feature is separate, e.g., `mfa.py`, `oauth.py`)
- Tests: `tests/test_<feature>.py`
- Export: Add to `src/ecotone_common/__init__.py`

**New Token Type:**
- Location: Add method to `TokenService` class in `src/ecotone_common/tokens.py`
- Pattern: Use existing `generate_*` and `validate_*` method signatures with appropriate salt and max_age
- Tests: Add test cases to `tests/test_tokens.py`

**New Email Backend:**
- Location: New class in `src/ecotone_common/email.py` inheriting from `EmailBackend`
- Pattern: Implement `send(to: str, subject: str, html_body: str) -> bool`
- Factory: Update `create_email_backend(config)` function to recognize config key and instantiate new backend
- Tests: Add to `tests/test_email.py` including factory selection logic

**New Password Validation Rule:**
- Location: `validate_strength()` function in `src/ecotone_common/passwords.py`
- Pattern: Add optional parameter (e.g., `require_special: bool = True`) and validation check
- Tests: Add test case to `tests/test_passwords.py` for new rule and custom thresholds

**New Consent Type:**
- Location: `src/ecotone_common/consent.py` - add helper function if SQL structure differs
- Pattern: Thin wrapper over cursor.execute() with schema expectations documented
- Tests: Add to `tests/test_consent.py` mocking cursor behavior

## Special Directories

**`.pytest_cache/`:**
- Purpose: pytest cache (test discovery, plugin state)
- Generated: Yes
- Committed: No (in .gitignore)

**`src/ecotone_common.egg-info/`:**
- Purpose: Package metadata (generated during `pip install -e .`)
- Generated: Yes
- Committed: No (in .gitignore)

**`__pycache__/` and `.pyc` files:**
- Purpose: Python bytecode cache
- Generated: Yes
- Committed: No (in .gitignore)

## Build & Installation

**Development Installation:**
```bash
pip install -e .              # Install package in editable mode
pip install -e ".[all]"       # Include optional sendgrid dependency
```

**Testing:**
```bash
python -m pytest              # Run all tests
python -m pytest tests/test_tokens.py  # Run specific test file
```

**Package Distribution:**
```bash
python -m build               # Create wheel and sdist
python -m twine upload dist/* # Upload to PyPI (requires credentials)
```

**Version Bumping:**
- Update version in `pyproject.toml` [project] section
- Currently at 0.1.0 (pre-release, active development)

## Import Paths

**From consuming app:**
```python
# Direct function imports
from ecotone_common import hash_password, check_password, validate_strength

# Class imports
from ecotone_common import TokenService
from ecotone_common import SmtpBackend, SendGridBackend, LogBackend, create_email_backend

# Consent utilities
from ecotone_common import log_consent, get_current_eula_version
```

**Internal module imports (within this package):**
```python
# From __init__.py to re-export:
from .passwords import hash_password, check_password, validate_strength
from .tokens import TokenService
from .email import SmtpBackend, SendGridBackend, LogBackend, create_email_backend
from .consent import log_consent, get_current_eula_version
```

**Test imports:**
```python
from ecotone_common import hash_password, TokenService
from ecotone_common.email import SmtpBackend, SendGridBackend, LogBackend, create_email_backend
from ecotone_common.consent import log_consent, get_current_eula_version
```

## Dependency Management

**Core Dependencies:**
- `bcrypt>=4.0`: Password hashing (imported in passwords.py)
- `itsdangerous>=2.0`: Signed tokens (imported in tokens.py)

**Optional Dependencies:**
- `sendgrid>=6.0`: SendGrid email API (optional, imported only if used in email.py)
- Standard library: logging, secrets, smtplib, email.mime (no version constraints)

**Python Version:**
- Requires Python >=3.11 (for modern union syntax `str | None`, type hints)
