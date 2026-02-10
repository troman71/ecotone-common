# Architecture

**Analysis Date:** 2026-02-10

## Pattern Overview

**Overall:** Stateless utility library (shared package)

**Key Characteristics:**
- No framework dependencies (Flask, Django agnostic)
- Caller-provided configuration (loose coupling)
- Single responsibility per module (passwords, tokens, email, consent)
- Designed to be pip-installable and reusable across Ecotone apps
- Zero global state - all services instantiated explicitly

## Layers

**Public API Layer:**
- Purpose: Exported functions and classes for consuming apps
- Location: `src/ecotone_common/__init__.py`
- Contains: Package exports (functions, classes, factories)
- Depends on: Internal modules
- Used by: Flask apps (ecotone-impact, ecotone-esg, mn-nonprofit-tool)

**Service Modules:**
- Purpose: Core logic for specific authentication/consent features
- Location: `src/ecotone_common/{passwords,tokens,email,consent}.py`
- Contains: Stateless functions and classes implementing feature logic
- Depends on: External libraries (bcrypt, itsdangerous, sendgrid, smtplib)
- Used by: Public API layer

**External Dependencies:**
- Purpose: Third-party crypto and messaging libraries
- Integrated: bcrypt (password hashing), itsdangerous (signed tokens), sendgrid (email API), smtplib (SMTP)

## Data Flow

**Password Hashing Workflow:**

1. Caller invokes `hash_password(password: str)`
2. Module encodes password to UTF-8
3. bcrypt generates random salt and hashes
4. Hash returned as UTF-8 string to caller
5. Caller stores hash in app's database

**Verification Workflow:**

1. Caller retrieves stored hash from database
2. Caller invokes `check_password(password, stored_hash)`
3. Module decodes both to bytes and compares with bcrypt
4. Returns boolean result

**Token Generation Workflow:**

1. Caller invokes `TokenService(secret_key)` constructor
2. TokenService wraps itsdangerous.URLSafeTimedSerializer
3. Caller invokes specialized token method: `generate_verification_token(email)`, `generate_reset_token(email)`, etc.
4. Method uses salted serialization to create signed, timestamped token
5. Token returned as URL-safe string to caller
6. Caller encodes token in email/URL/response

**Token Validation Workflow:**

1. Caller retrieves token from user input (email link, form, etc.)
2. Caller invokes corresponding validation method: `validate_verification_token(token, max_age=3600)`
3. Module attempts deserialization with salt and max_age constraints
4. Returns extracted data (email, dict with user_id/action) or None on failure
5. Caller acts based on result

**Email Sending Workflow:**

1. App calls `create_email_backend(config)` factory at startup
2. Factory checks for SENDGRID_API_KEY → SendGridBackend, or SMTP_HOST → SmtpBackend, or LogBackend (fallback)
3. Backend instance stored in app context/globals
4. When email needed: `backend.send(to, subject, html_body)`
5. Backend sends via appropriate transport (API, SMTP, or logging)
6. Returns boolean success

**Consent Logging Workflow:**

1. Caller obtains database cursor (psycopg2 or compatible)
2. Caller invokes `log_consent(cursor, user_id, consent_type, version, accepted, ip_address, user_agent)`
3. Function executes INSERT into app's `consent_log` table
4. For EULA version lookup: `get_current_eula_version(cursor)`
5. Query runs against app's `eula_versions` table
6. Returns latest version string or None

**State Management:**
- No persistent state in library itself
- TokenService maintains only URLSafeTimedSerializer instance (stateless wrapper around secret key)
- Email backends maintain only configuration (host, credentials, etc.)
- Consent operations execute immediately; caller manages database connection lifecycle

## Key Abstractions

**TokenService:**
- Purpose: Time-limited, signed token generation and validation for auth workflows
- Examples: `src/ecotone_common/tokens.py`
- Pattern: Wrapper around itsdangerous.URLSafeTimedSerializer with typed methods for each use case (verification, reset, approval, invitations)
- Encapsulates: Salt selection, max_age defaults, exception handling (SignatureExpired, BadSignature)

**EmailBackend (abstract base):**
- Purpose: Pluggable email transport abstraction
- Examples: `src/ecotone_common/email.py` (SmtpBackend, SendGridBackend, LogBackend)
- Pattern: Strategy pattern - caller uses factory `create_email_backend(config)` to select implementation at startup
- Encapsulates: SMTP vs API differences, configuration discovery, failure handling

**Password Utilities (functional):**
- Purpose: bcrypt-based password security functions
- Examples: `src/ecotone_common/passwords.py`
- Pattern: Pure functions with sensible defaults (8-char minimum, upper+lower+digit required)
- Encapsulates: String encoding (UTF-8), bcrypt round count, validation logic

**Consent Helpers (functional):**
- Purpose: Audit trail and EULA version tracking
- Examples: `src/ecotone_common/consent.py`
- Pattern: Thin wrappers over SQL - caller provides cursor, functions execute directly
- Encapsulates: SQL structure, cursor type detection (dict vs tuple), schema assumptions

## Entry Points

**Package Imports:**
- Location: `src/ecotone_common/__init__.py`
- Triggers: `from ecotone_common import hash_password, TokenService, create_email_backend, log_consent`
- Responsibilities: Re-export public API, version string

**TokenService Class:**
- Location: `src/ecotone_common/tokens.py`
- Triggers: `ts = TokenService(secret_key)` at app startup
- Responsibilities: Hold secret key, provide token generation/validation methods

**Email Backend Factory:**
- Location: `src/ecotone_common/email.py` function `create_email_backend()`
- Triggers: App calls at startup with config dict
- Responsibilities: Select and instantiate appropriate backend

**Consent Functions:**
- Location: `src/ecotone_common/consent.py`
- Triggers: App calls `log_consent()` after user accepts terms, `get_current_eula_version()` before presenting form
- Responsibilities: Execute INSERT/SELECT against app database

## Error Handling

**Strategy:** Fail-fast on invalid input; graceful None return on expiry/signature failure; exceptions bubble up for infrastructure issues

**Patterns:**

- **Token Validation:** Returns None if signature invalid or expired (tested by caller)
  ```python
  def validate_verification_token(token: str, max_age: int = 3600) -> str | None:
      try:
          return self._serializer.loads(token, salt='email-verify', max_age=max_age)
      except SignatureExpired:
          logger.warning("Verification token expired")
          return None
      except BadSignature:
          logger.warning("Invalid verification token")
          return None
  ```

- **Email Sending:** Returns boolean; caller decides on retry/notification logic
  ```python
  def send(self, to: str, subject: str, html_body: str) -> bool:
      # SmtpBackend: raises on network/auth failure
      # SendGridBackend: checks status_code, returns False on error
      # LogBackend: always returns True
  ```

- **Password Validation:** Returns list of failure messages; empty list = valid
  ```python
  def validate_strength(...) -> list[str]:
      failures = []
      if len(password) < min_length:
          failures.append(...)
      return failures  # caller iterates to display errors
  ```

- **Consent Logging:** No explicit error handling; psycopg2 exceptions propagate (caller handles DB issues)

## Cross-Cutting Concerns

**Logging:** Minimal use via Python logging module
- TokenService logs warning when token validation fails (expired/invalid signature)
- Email backends log info on send, error on SendGrid API failure
- No debug logging; caller can enable module-level via `logging.getLogger('ecotone_common').setLevel(...)`

**Validation:** Module-specific, no central validator
- Password: strength rules (length, character classes) with configurable thresholds
- Tokens: itsdangerous library validates signature and expiry
- Email: No validation of email address format (caller responsibility)
- Consent: No validation (assumes app provides valid user_id, consent_type, version)

**Authentication:** Not applicable - library provides primitives, not enforcement
- Caller decides where to place token validation (middleware, route decorator, etc.)
- Library only provides token generation and verification methods

**Database Access:** Consent module assumes caller owns database connection
- No connection pooling, ORM, or transaction management in library
- Caller passes cursor and manages lifecycle (connection, rollback, commit)
- Supports both psycopg2 dict cursors and tuple cursors
