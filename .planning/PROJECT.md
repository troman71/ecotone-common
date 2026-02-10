# ecotone-common

## What This Is

A shared pip-installable Python package providing authentication utilities (email sending, password hashing, token generation, consent logging) used across all Ecotone Flask applications (Impact, ESG, Better Futures Materials). Zero Flask dependency — pure Python library that apps wire into their own frameworks.

## Core Value

Every Ecotone app uses identical, well-tested auth primitives — no drift, no duplication, one place to fix bugs or upgrade security.

## Current State

Shipped v0.1.0 with 593 LOC Python.
Tech stack: bcrypt, itsdangerous, ruff, pytest, GitHub Actions.
4 modules: passwords, tokens, email, consent.
32 passing tests, CI on Python 3.11/3.12/3.13.
In production use by ecotone-impact.

## Requirements

### Validated

- ✓ Password hashing and verification via bcrypt — existing
- ✓ Password strength validation with configurable rules — existing
- ✓ Token generation/validation (verification, reset, approval, invite) via itsdangerous — existing
- ✓ Email sending via SMTP backend (Gmail) — existing
- ✓ Email sending via SendGrid backend — existing
- ✓ Log-only email backend for development — existing
- ✓ Email backend factory (auto-select from config) — existing
- ✓ Consent logging helper (cursor-based DB insert) — existing
- ✓ EULA version lookup helper — existing
- ✓ 32 passing tests across all modules — existing
- ✓ Installed and working in ecotone-impact — existing
- ✓ GitHub Actions CI with pytest + ruff linting — v0.1
- ✓ v0.1.0 annotated git tag for release tracking — v0.1
- ✓ README.md with install instructions and per-module API examples — v0.1
- ✓ CHANGELOG.md tracking changes per version — v0.1

### Active

- [ ] Harden email backends (error handling, `__repr__` masking)
- [ ] Add SMTP/SendGrid error case tests
- [ ] Add `__repr__` to backends to prevent credential leaks in logs

### Out of Scope

- DB helpers / tenant isolation — app-specific, stays in each app
- Config loading / env parsing — apps handle their own config
- Flask integration (decorators, middleware) — this is a plain Python library
- PyPI publishing — overkill for 3 internal apps, use git clone + editable install
- Async support — all consuming apps are sync Flask

## Context

- Three Ecotone Flask apps duplicate auth code: Impact, ESG, Better Futures Materials
- Architecture decision (ARCHITECTURE_PATTERNS_DECISION_RECORD.md, Decision 1) called for extracting shared services
- Impact is the first adopter (migrated 2026-02-10), ESG and BFM migrations in progress
- Package is consumed via `pip install -e /path/to/ecotone-common` locally and `git clone` in CI
- Repo is private (troman71/ecotone-common), CI access via GH_PAT secret

## Constraints

- **No Flask dependency**: Must remain a plain Python library — apps pass in their own cursors/config
- **No breaking changes**: Impact is already using this in production code
- **Python >=3.11**: All Ecotone apps run 3.11+
- **Backward compatible salts**: Token salts ('email-verify', 'password-reset', 'approval-action') must not change — existing tokens in the wild would break

## Key Decisions

| Decision | Rationale | Outcome |
|----------|-----------|---------|
| pip-installable package over git submodule or monorepo | Cleanest dependency management, standard Python tooling | ✓ Good |
| No Flask dependency | Keeps package portable across any Python web framework | ✓ Good |
| Editable local install for dev, git clone for CI | Simple, no PyPI infrastructure needed for 3 apps | ✓ Good |
| SmtpBackend raises exceptions (caller handles) | Matches Impact's existing try/except pattern in email_service.py | — Pending |
| Ruff over Flake8 for linting | 50-150x faster, single tool for lint + format | ✓ Good |
| Annotated git tags for releases | Preserves author, date, message metadata for production tracking | ✓ Good |
| __all__ export list in __init__.py | Proper public API, fixes F401 violations, helps IDE autocomplete | ✓ Good |

---
*Last updated: 2026-02-10 after v0.1 milestone*
