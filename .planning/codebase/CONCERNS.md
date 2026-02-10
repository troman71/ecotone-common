# Codebase Concerns

**Analysis Date:** 2026-02-10

## Error Handling & Robustness

**SMTP Backend has no exception handling:**
- Issue: `SmtpBackend.send()` in `src/ecotone_common/email.py` (lines 46-52) performs critical SMTP operations without try/except. Network failures, authentication errors, or connection timeouts will bubble up as unhandled exceptions.
- Files: `src/ecotone_common/email.py`
- Impact: Email sending fails silently to callers without context. Application code must wrap sends in their own try/except or face crashes. No retry logic, no graceful degradation.
- Fix approach: Add try/except blocks around `server.starttls()`, `server.login()`, and `server.sendmail()`. Log specific error types. Return False on failure (matching the interface contract). Consider adding optional retry logic.

**SendGrid Backend has incomplete error handling:**
- Issue: `SendGridBackend.send()` in `src/ecotone_common/email.py` (lines 77-83) only checks for success codes (200, 201, 202). Non-2xx responses are logged but the method continues and may mask transient failures.
- Files: `src/ecotone_common/email.py`
- Impact: Silent failures on rate limits (429), temporary unavailability (5xx), or malformed requests (4xx). Callers see False but don't know why.
- Fix approach: Log response body for debugging. Consider specific handling for retryable vs. fatal errors (429/5xx vs. 400/401). Document expected error codes in comments.

**No exception handling on email send() calls:**
- Issue: Callers of `SmtpBackend.send()` must handle potential exceptions (socket.error, SMTPException, etc.) but the method signature doesn't document this.
- Files: `src/ecotone_common/email.py` (interface defined at line 17)
- Impact: Developers importing this package may assume send() is safe to call without wrapping. Unhandled exceptions crash applications.
- Fix approach: Document that send() may raise exceptions, or wrap all SMTP operations in try/except and return False with logged context.

## Security Considerations

**Logging of sensitive token data:**
- Issue: `TokenService` in `src/ecotone_common/tokens.py` (lines 31, 34, 48, 51, 65, 68, 85, 88) logs warnings with salt names on token validation failures. The salt is used to bind specific token types (e.g., 'email-verify', 'password-reset'). While salts are not secrets, logging them reveals which auth workflow failed, which could aid targeted attacks.
- Files: `src/ecotone_common/tokens.py`
- Impact: Low risk, but unnecessary information leak in logs.
- Fix approach: Remove salt from warning logs. Log only "Token validation failed" without context that identifies the workflow.

**SMTP password stored in backend instance:**
- Issue: `SmtpBackend.__init__()` in `src/ecotone_common/email.py` (line 30) stores plaintext password as instance variable. If the backend object is logged, serialized, or dumped, the password is exposed.
- Files: `src/ecotone_common/email.py`
- Impact: Medium risk. Unlikely in typical usage, but serialization (e.g., debugging, profilers) could leak credentials.
- Fix approach: Store password as None after use. Better: fetch from environment/secrets manager on each send(). Implement `__repr__()` to mask password.

**SendGrid API key stored in backend instance:**
- Issue: `SendGridBackend.__init__()` in `src/ecotone_common/email.py` (line 59) stores API key as instance variable. Same serialization/logging risk as above.
- Files: `src/ecotone_common/email.py`
- Impact: Medium risk. API keys can be revoked but are high-value targets.
- Fix approach: Implement `__repr__()` to mask api_key. Store as None after first use if re-reads are not needed.

**Cursor passed to consent functions without validation:**
- Issue: `log_consent()` and `get_current_eula_version()` in `src/ecotone_common/consent.py` accept cursor objects directly from callers (lines 8, 19). No validation that the cursor is from the correct database, or that tables exist.
- Files: `src/ecotone_common/consent.py`
- Impact: Low risk in happy path. If caller passes wrong cursor (e.g., wrong database, different schema), errors are deferred to query execution time, making debugging harder.
- Fix approach: Add optional schema validation or document strict assumptions about cursor source and available tables.

## Test Coverage Gaps

**SMTP backend error cases not tested:**
- What's not tested: Connection failures, login failures, starttls failures, sendmail failures. SmtpBackend is mocked in tests, so no real failure modes are exercised.
- Files: `tests/test_email.py`
- Risk: Exceptions from SMTP operations in production will surprise developers who never tested them locally.
- Priority: Medium

**SendGrid backend error cases not tested:**
- What's not tested: Non-2xx response codes, network failures, malformed request parameters. Only success path (200-202) is mocked.
- Files: `tests/test_email.py`
- Risk: 429 (rate limit), 5xx (service down), and 400 (bad request) responses are not validated. Code assumes False return on any error, but doesn't test it.
- Priority: Medium

**Email backend integration not tested:**
- What's not tested: Actual SMTP connection (requires test account), actual SendGrid API call (requires API key).
- Files: `tests/test_email.py`
- Risk: Both backends could fail in production despite passing unit tests. Integration tests with mocked HTTP/SMTP are needed.
- Priority: Low (integration tests are optional for shared libraries)

**Token expiry edge cases not tested:**
- What's not tested: Tokens generated at second boundary (clock skew), tokens with max_age=0 (already expired), extremely old tokens (years old).
- Files: `tests/test_tokens.py`
- Risk: Time-based edge cases could cause intermittent failures in production.
- Priority: Low (existing tests cover the happy path and basic expiry)

**Consent logging doesn't test actual table constraints:**
- What's not tested: IP address field cast to inet type (`::inet` in SQL), database constraints on user_id/consent_type/version. Tests mock cursor, so schema violations aren't caught.
- Files: `tests/test_consent.py`
- Risk: If calling code passes invalid data or tables are missing columns, errors are deferred to runtime.
- Priority: Low (caller's responsibility to ensure schema matches)

**Password strength validation lacks special character requirement:**
- What's not tested: Special characters (!, @, #, etc.). Current validation only checks length, uppercase, lowercase, digit.
- Files: `src/ecotone_common/passwords.py`, `tests/test_passwords.py`
- Risk: Passwords like "Abcdef1g" pass validation but are vulnerable to dictionary attacks. Many standards (OWASP, PCI-DSS) recommend special characters.
- Priority: Medium (depends on security requirements of calling application)

## Dependencies & Compatibility

**SendGrid is an optional dependency with no fallback warning:**
- Issue: SendGrid is imported inside `SendGridBackend.send()` (line 64 of `src/ecotone_common/email.py`), not at module load time. If not installed, the error only surfaces when send() is called.
- Files: `src/ecotone_common/email.py`
- Impact: Low runtime risk (factory function falls back to LogBackend if sendgrid not configured). But if developer accidentally configures SendGridBackend without installing sendgrid, the error is delayed.
- Fix approach: Add validation in `create_email_backend()` to check that sendgrid is importable if SENDGRID_API_KEY is set. Or lazily import at module level with try/except.

**bcrypt version pinned loosely:**
- Issue: `pyproject.toml` (line 11) specifies `bcrypt>=4.0` with no upper bound. bcrypt 5.x or 6.x may introduce breaking changes.
- Files: `pyproject.toml`
- Impact: Low (bcrypt maintains backward compatibility well). But consumer apps could inherit incompatible bcrypt versions.
- Fix approach: Pin to known-compatible range (e.g., `bcrypt>=4.0,<6.0`) or add integration tests against new bcrypt versions.

**itsdangerous version pinned loosely:**
- Issue: `pyproject.toml` (line 12) specifies `itsdangerous>=2.0` with no upper bound.
- Files: `pyproject.toml`
- Impact: Low (itsdangerous 2.x is stable). But same risk as bcrypt.
- Fix approach: Pin to range (e.g., `itsdangerous>=2.0,<3.0`).

**No Python upper bound:**
- Issue: `pyproject.toml` (line 9) specifies `requires-python = ">=3.11"` with no upper bound. Code uses type hints with `|` syntax (Python 3.10+) and may silently break on Python 4.0+ if language changes.
- Files: `pyproject.toml`
- Impact: Low (Python 4.0 is years away). But good practice to declare tested versions.
- Fix approach: Declare tested range (e.g., `requires-python = ">=3.11,<4.0"`) once Python 3.12+ have been validated.

## Performance Considerations

**No connection pooling in SMTP backend:**
- Issue: `SmtpBackend.send()` creates a new SMTP connection for each email (line 46 of `src/ecotone_common/email.py`). No connection reuse or pooling.
- Files: `src/ecotone_common/email.py`
- Impact: High latency for batch operations (e.g., sending 100 verification emails). Each email waits for TCP connect, TLS handshake, auth.
- Improvement path: Provide optional connection pooling (e.g., accept optional SMTP connection pool from caller). Document that send() is synchronous and blocking. Recommend async wrapper for batch sends.

**No async support:**
- Issue: All email backends and token operations are synchronous. No async variants.
- Files: `src/ecotone_common/email.py`, `src/ecotone_common/tokens.py`
- Impact: Calling async applications (FastAPI, aiohttp) must wrap these calls in thread pool. Scales poorly under high concurrency.
- Improvement path: Add async variants (async_send() method or separate async backends). This is a breaking change, so consider for 1.0 release.

## Fragile Areas

**Cursor type detection in consent:**
- Files: `src/ecotone_common/consent.py` (lines 27-30)
- Why fragile: Code checks `isinstance(row, dict)` to distinguish between dict-like and tuple cursors. This assumes all callers use either psycopg2 DictCursor (dict) or standard Cursor (tuple). Custom cursor classes or RealDictCursor variants may not match either condition.
- Safe modification: Add explicit type hints or accept cursor factory function instead of raw cursor. Or document supported cursor types (psycopg2 Cursor, DictCursor only).

**Email backend factory relies on config key presence:**
- Files: `src/ecotone_common/email.py` (lines 99-124)
- Why fragile: Factory checks `config.get('SENDGRID_API_KEY')` first, then `config.get('SMTP_HOST')`, then defaults to LogBackend. If SMTP_HOST is set but SENDGRID_API_KEY is present (even if empty or falsy), SendGrid backend is chosen. Edge case: `SENDGRID_API_KEY=''` (empty string) is falsy but presence is checked.
- Safe modification: Explicitly check `if config.get('SENDGRID_API_KEY') and config['SENDGRID_API_KEY']` to avoid empty strings. Or accept backend type as explicit parameter instead of inferring from keys.

**Token service has hardcoded salt strings:**
- Files: `src/ecotone_common/tokens.py` (lines 41, 58, 77)
- Why fragile: Salt strings ('email-verify', 'password-reset', 'approval-action') are hardcoded. If a developer copies TokenService to a different project and changes the salt string, tokens generated before the change become unvalidatable (signature changes with salt).
- Safe modification: Document that salts are part of the token contract and should never be changed. Consider moving salts to class constants or requiring them as parameters.

## Known Limitations

**No rate limiting in token validation:**
- Issue: `TokenService.validate_*_token()` methods don't track failed attempts. A caller could brute-force tokens (unlikely due to signature scheme, but theoretical).
- Files: `src/ecotone_common/tokens.py`
- Current mitigation: itsdangerous signatures are cryptographically secure; brute-force requires high entropy.
- Recommendations: Document that callers should implement rate limiting on token validation endpoints. Token endpoints should not expose whether a token is expired vs. invalid (timing attack).

**Password strength is low by modern standards:**
- Issue: Default minimum length is 8 characters, no special characters required, no common password dictionary checked.
- Files: `src/ecotone_common/passwords.py`
- Current mitigation: Calling applications can configure min_length and require_* flags. NIST guidelines recommend 12+ characters or passphrases.
- Recommendations: Update defaults to min_length=12 or add zxcvbn integration for entropy checking. Document as security policy for consuming applications.

**No secrets rotation mechanism:**
- Issue: TokenService and email backends store secrets (secret_key, api_key, password) for the lifetime of the object. No key rotation support.
- Files: `src/ecotone_common/tokens.py`, `src/ecotone_common/email.py`
- Current mitigation: Secrets should be managed by deployment (environment variables, secrets manager). This library is stateless.
- Recommendations: Document that if secrets change in production, new instances of TokenService/backend must be created. Consider adding hook for dynamic secret fetching.

## Missing Features

**No logging configuration:**
- Issue: Package defines loggers (`logger = logging.getLogger(__name__)`) but doesn't configure logging (handlers, formatters). Caller must configure.
- Files: `src/ecotone_common/email.py`, `src/ecotone_common/tokens.py`
- Impact: Logs may be silently discarded if calling application hasn't configured logging.
- Recommendation: Add optional logging setup helper or document that caller must configure logging (standard practice for libraries).

**No metrics/observability:**
- Issue: No hooks for counting sends, measuring token validation latency, or tracking errors.
- Impact: Calling applications must instrument manually.
- Recommendation: Add optional callback parameters (e.g., `on_email_sent`, `on_token_validated`) or integrate with OpenTelemetry.

---

*Concerns audit: 2026-02-10*
