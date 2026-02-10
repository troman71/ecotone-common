# External Integrations

**Analysis Date:** 2026-02-10

## APIs & External Services

**Email Delivery:**
- SendGrid - Optional email delivery service
  - SDK/Client: `sendgrid>=6.0` (optional, lazy-imported)
  - Location: `src/ecotone_common/email.py:SendGridBackend`
  - Auth: `SENDGRID_API_KEY` (passed via config dict, not from env)
  - Usage: Production email sending for verification links, password resets, notifications
  - Alternative: SMTP backend for any SMTP provider (Gmail, custom servers)

## Data Storage

**Databases:**
- PostgreSQL (intended consumer, not required by package)
  - Connection: Caller provides psycopg2 cursor via function arguments
  - Consumer apps: ecotone-impact, ecotone-esg use Cloud SQL
  - Tables required by consent module: `consent_log`, `eula_versions`
  - Location: `src/ecotone_common/consent.py:log_consent()`, `get_current_eula_version()`
  - Pattern: Package provides helper functions; caller manages connection

**File Storage:**
- None - Package is stateless

**Caching:**
- None - Package does not implement or require caching

## Authentication & Identity

**Auth Provider:**
- Custom JWT + EULA flow (see related projects)
  - Implementation: Provided by consuming Flask apps (ecotone-esg, mn-nonprofit-tool)
  - This package provides token utilities for: email verification, password reset, approval actions, invitations
  - Token generation: `src/ecotone_common/tokens.py:TokenService`
  - No external identity provider dependency (e.g., Auth0, Okta)

**Password Security:**
- bcrypt-based hashing (no external service)
  - Implementation: `src/ecotone_common/passwords.py`
  - Strength validation rules configurable per caller

## Monitoring & Observability

**Error Tracking:**
- None - Package does not send error reports
- Logging: Via Python standard `logging` module
  - Log levels used: INFO (successful operations), WARNING (token expiry, invalid signatures), ERROR (SendGrid failures)
  - Location: `src/ecotone_common/tokens.py`, `src/ecotone_common/email.py`

**Logs:**
- To Python logger (caller configures output destination)
- Log messages: Token validation failures, email send status, consent records

## CI/CD & Deployment

**Hosting:**
- Distributed via PyPI (not yet published, intended as private package)
- Installation: `pip install ecotone-common` or from git

**CI Pipeline:**
- None currently configured in this repo
- Consuming apps (ecotone-impact, ecotone-esg) have CI that tests against this package

## Environment Configuration

**Required env vars:**
- None required at package level
- All config passed explicitly via constructor or factory function arguments

**Optional env vars (managed by consumer):**
- `SENDGRID_API_KEY` - Only if using SendGridBackend
- `SMTP_HOST`, `SMTP_PORT`, `SMTP_USERNAME`, `SMTP_PASSWORD` - Only if using SmtpBackend
- `FROM_EMAIL`, `FROM_NAME` - If email backends are used

**Secrets location:**
- Not applicable - Package does not manage secrets
- Consuming app (.env or cloud secret manager) supplies credentials to `create_email_backend()` factory

## Webhooks & Callbacks

**Incoming:**
- None - Package is a library, not a service

**Outgoing:**
- None - Package does not make external API calls except via SendGrid (on demand)

## SMTP Configuration

**Standard SMTP Support:**
- SmtpBackend (`src/ecotone_common/email.py:22-52`)
- Compatible with: Gmail, custom mail servers, any SMTP provider
- Configurable port (default 587 with STARTTLS)
- Custom from address and display name support
- Implementation: Python standard `smtplib` module

**Email Format:**
- HTML emails only (MIMEMultipart with HTML content)
- MIME type: `text/html`
- From address: Configurable, defaults to username

## SendGrid Configuration

**API Integration:**
- SendGridBackend (`src/ecotone_common/email.py:55-83`)
- Uses sendgrid Python SDK (lazy import on first use)
- API endpoint: sendgrid.SendGridAPIClient (https://api.sendgrid.com/v3/)
- Success codes: 200, 201, 202
- Error logging: Returns False on non-2xx responses

**SendGrid Classes Used:**
- `Mail` - Message builder
- `Email` - Address object
- `To` - Recipient wrapper
- `Content` - Message content (HTML)

## Consent & EULA Logging

**Database Tables Required:**
- `consent_log` - Audit trail of consent actions
  - Columns: user_id, consent_type, version, accepted, ip_address, user_agent, created_at (implicit)
  - Example: `log_consent(cursor, 123, 'eula', '1.0', True, '192.168.1.1', 'Mozilla/5.0...')`
  - Location: `src/ecotone_common/consent.py:8-16`

- `eula_versions` - EULA version registry
  - Columns: version (string), effective_date (date)
  - Query: `SELECT version FROM eula_versions ORDER BY effective_date DESC LIMIT 1`
  - Location: `src/ecotone_common/consent.py:19-30`

**Cursor Flexibility:**
- Supports both dict-like (DictCursor) and tuple cursors
- See: `src/ecotone_common/consent.py:28-30`

## No Third-Party Dependencies Required

This package has **zero runtime integrations** beyond those explicitly configured:
- Email delivery is optional (SendGrid or SMTP)
- Database operations are caller-managed
- No telemetry, no API calls, no cloud integrations
- Pure utility library intended for reuse across Ecotone applications

---

*Integration audit: 2026-02-10*
