# Technology Stack

**Analysis Date:** 2026-02-10

## Languages

**Primary:**
- Python 3.11+ - All source code and tests

## Runtime

**Environment:**
- Python 3.11 (enforced via `requires-python` in pyproject.toml)
- Standard library only (no runtime dependency on Flask or other frameworks)

**Package Manager:**
- pip (implicit via setuptools)
- Lockfile: Not committed (no lock file in repo)

## Frameworks

**Core:**
- setuptools 68.0+ - Package building and distribution
- No web framework dependency (intentional - library is framework-agnostic)

**Testing:**
- pytest - Unit test runner
- Config: Default (no pytest.ini or pyproject.toml pytest section)
- Tests located in `tests/` directory

**Build/Dev:**
- wheel - Package distribution format (part of build-system)

## Key Dependencies

**Critical:**
- `bcrypt>=4.0` - Password hashing
  - Used in `src/ecotone_common/passwords.py`
  - Implements bcrypt password hashing and verification
  - Why it matters: Core security utility for all Flask apps using this package

- `itsdangerous>=2.0` - Signed token generation and validation
  - Used in `src/ecotone_common/tokens.py`
  - Implements URLSafeTimedSerializer for time-limited signed tokens
  - Why it matters: Enables email verification, password reset, approval workflows without database state

**Optional:**
- `sendgrid>=6.0` - SendGrid email API client
  - Optional dependency for production email delivery
  - Used in `src/ecotone_common/email.py` (SendGridBackend class)
  - Only imported when SendGridBackend is instantiated
  - Installed via `pip install ecotone-common[sendgrid]` or `pip install ecotone-common[all]`

## Configuration

**Environment:**
- Framework-agnostic - Configuration passed to constructors, not read from environment
- Email backend created via factory function `create_email_backend(config: dict)`
  - Caller provides config dict with keys like `SENDGRID_API_KEY`, `SMTP_HOST`, `FROM_EMAIL`
  - See `src/ecotone_common/email.py:99-124`

**Database:**
- No database dependencies in package
- Consent logging functions (`src/ecotone_common/consent.py`) expect caller to provide cursor
  - Tables `consent_log` and `eula_versions` must exist in consuming app's database
  - Functions are pure helpers - no connection management

## Package Structure

**Entry Point:**
- `src/ecotone_common/` - Main package directory
  - `__init__.py` - Public API exports
  - `passwords.py` - Password hashing utilities
  - `tokens.py` - Token generation and validation (TokenService)
  - `email.py` - Email backends (SMTP, SendGrid, Log)
  - `consent.py` - Consent and EULA logging helpers

**Tests:**
- `tests/` - Unit tests using pytest
  - `test_passwords.py` - Password hashing and validation tests
  - `test_tokens.py` - Token generation/expiry/validation tests
  - `test_email.py` - Email backend tests (mocked SMTP/SendGrid)
  - `test_consent.py` - Consent logging tests

## Platform Requirements

**Development:**
- Python 3.11 or higher
- pip for package installation
- pytest for running tests
- Optional: sendgrid package for testing SendGrid integration

**Production:**
- Python 3.11 or higher
- bcrypt, itsdangerous packages installed
- Optional: sendgrid package if using SendGridBackend
- Intended to be installed as dependency in Flask applications (ecotone-impact, ecotone-esg, etc.)

## No External Service Dependencies

This package is **self-contained**. It does not:
- Connect to databases (caller provides cursor for consent logging)
- Make HTTP requests (SendGrid import is lazy, only on use)
- Require environment variables (all config passed explicitly)
- Depend on Flask or any web framework
- Require cloud infrastructure (except optional SendGrid account)

---

*Stack analysis: 2026-02-10*
