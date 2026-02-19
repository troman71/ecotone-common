# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/),
and this project adheres to [Semantic Versioning](https://semver.org/).

## [Unreleased]

### Added

- `passwords.needs_rehash(hashed)` -- returns True if hash should be upgraded to bcrypt

### Changed

- `passwords.check_password()` now supports legacy werkzeug hashes (scrypt, pbkdf2) in addition to bcrypt. Callers no longer need to detect hash format manually.

## [0.1.0] - 2026-02-10

### Added

- `passwords` module: `hash_password()`, `check_password()`, `validate_strength()` using bcrypt
- `tokens` module: `TokenService` class with signed token generation/validation for email verification, password reset, admin approval, and team invitations (uses itsdangerous)
- `email` module: `SmtpBackend`, `SendGridBackend`, `LogBackend` email backends with `create_email_backend()` factory
- `consent` module: `log_consent()` and `get_current_eula_version()` helpers for EULA/consent tracking
- 32 passing tests across all modules
- CI/CD: GitHub Actions workflow with pytest and ruff on Python 3.11/3.12/3.13
- Package configuration via pyproject.toml (src layout, Python 3.11+)
