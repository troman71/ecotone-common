# Testing Patterns

**Analysis Date:** 2026-02-10

## Test Framework

**Runner:**
- pytest (inferred from `.pytest_cache` directory)
- No `pytest.ini` or `[tool.pytest.ini_options]` in `pyproject.toml`
- Config: Default pytest configuration

**Assertion Library:**
- Python `assert` statements (built-in)

**Run Commands:**
```bash
python -m pytest tests/                    # Run all tests
python -m pytest tests/ -v                 # Verbose output
python -m pytest tests/ --cov              # With coverage (if pytest-cov installed)
python -m pytest tests/ -k test_name       # Run single test by name
python -m pytest tests/ -x                 # Stop on first failure
```

## Test File Organization

**Location:**
- Tests co-located in `tests/` directory parallel to `src/`
- Not embedded alongside source files

**Naming:**
- Test files: `test_*.py` prefix
- Test functions: `test_*` prefix
- Module correspondence: `test_passwords.py` tests `passwords.py`, etc.

**Structure:**
```
tests/
├── test_passwords.py      # Tests for passwords module
├── test_tokens.py         # Tests for tokens module
├── test_email.py          # Tests for email module
└── test_consent.py        # Tests for consent module
```

## Test Structure

**Suite Organization:**

Tests follow a flat function-based structure. No class-based test suites.

**Example from `tests/test_passwords.py`:**
```python
def test_hash_and_check():
    hashed = hash_password('MySecret123')
    assert check_password('MySecret123', hashed)
    assert not check_password('WrongPassword', hashed)


def test_hash_returns_string():
    hashed = hash_password('test')
    assert isinstance(hashed, str)
    assert hashed.startswith('$2b$')
```

**Patterns:**
- No explicit setup/teardown (no pytest fixtures defined)
- Each test creates its own objects: `ts = TokenService('test-secret')`
- Tests are independent and can run in any order
- No shared state between tests

## Mocking

**Framework:** `unittest.mock` from Python standard library

**Patterns:**

Mock SMTP connection:
```python
with patch('ecotone_common.email.smtplib.SMTP') as mock_smtp:
    ctx = MagicMock()
    mock_smtp.return_value.__enter__ = MagicMock(return_value=ctx)
    mock_smtp.return_value.__exit__ = MagicMock(return_value=False)
    result = backend.send('to@example.com', 'Subject', '<p>Body</p>')
```

From `tests/test_email.py:19-38`, standard context manager mocking pattern.

Mock database cursor:
```python
cursor = MagicMock()
log_consent(cursor, 'user-123', 'eula', '1.0', True, '1.2.3.4', 'Mozilla/5.0')
cursor.execute.assert_called_once()
```

From `tests/test_consent.py:7-13`, mock object with assertion verification.

**What to Mock:**
- External dependencies: `smtplib.SMTP`, database cursors
- Network calls: SendGrid API (via mocked response)
- Time: Use `time.sleep()` to test expiration (see below)

**What NOT to Mock:**
- Core cryptographic operations: Test real `bcrypt` hashing
- Token generation: Use real `TokenService` with test secrets
- Password validation: Test actual logic, not mocked behavior
- Email backend factory: Test real backend selection logic

## Fixtures and Factories

**Test Data:**

No pytest fixtures defined. Instead, factories are inline in test functions.

Example from `tests/test_tokens.py:7-10`:
```python
def test_verification_token_roundtrip():
    ts = TokenService('test-secret')
    token = ts.generate_verification_token('user@example.com')
    assert ts.validate_verification_token(token) == 'user@example.com'
```

Common test data:
- Email addresses: `'user@example.com'`, `'test@example.com'`, `'to@example.com'`
- Passwords: `'MySecret123'`, `'Abcdef1x'`, `'password1'`
- User IDs: `'user-123'`, `'user-456'`, strings
- Tokens: Generated on-the-fly within test

**Location:**
- No separate fixture file; factories defined inline in tests
- Reduces boilerplate for this small package

## Coverage

**Requirements:** Not enforced

No coverage requirements detected in `pyproject.toml` or pytest config.

**View Coverage:**
```bash
python -m pytest tests/ --cov=src/ecotone_common --cov-report=html
python -m pytest tests/ --cov=src/ecotone_common --cov-report=term
```

(Requires `pytest-cov` package; not listed in dependencies but commonly installed.)

**Current Coverage:**
- High coverage observed: core functions extensively tested
- `passwords.py`: All functions tested (hash, check, validate_strength with variations)
- `tokens.py`: All token types tested (verification, reset, approval, generic, invite)
- `email.py`: All backends tested (Log, SMTP with mocking, SendGrid with mocking, factory)
- `consent.py`: All functions tested (log_consent, get_current_eula_version with dict/tuple cursors)

## Test Types

**Unit Tests:**
- Scope: Single module/function at a time
- Approach: Pure unit testing with minimal mocking
- Example: `test_hash_and_check()` tests `hash_password()` and `check_password()` in isolation
- Execution: Fast, no external I/O except mocked calls

**Integration Tests:**
- Not present in current test suite
- Would test multiple modules together (e.g., token generation + validation with email)
- Could be added in future phases

**E2E Tests:**
- Not applicable to this package; it's a utility library, not a web app
- Consumers (Flask apps) would have E2E tests for features using these utilities

## Common Patterns

**Async Testing:**
- Not applicable; no async code in package
- All functions are synchronous

**Time-Based Testing:**

Pattern from `tests/test_tokens.py:13-17`:
```python
def test_verification_token_expired():
    ts = TokenService('test-secret')
    token = ts.generate_verification_token('user@example.com')
    time.sleep(2)
    assert ts.validate_verification_token(token, max_age=1) is None
```

- Sleep for 2 seconds
- Validate with `max_age=1` to trigger expiration
- Assert returns `None` (invalid token)

**Error Testing:**

Pattern from `tests/test_passwords.py:32-34`:
```python
def test_validate_strength_too_short():
    errors = validate_strength('Ab1')
    assert any('8 characters' in e for e in errors)
```

- Call function with invalid input
- Assert error list contains expected message
- Use `any()` with substring matching for robustness

Pattern from `tests/test_tokens.py:20-24`:
```python
def test_verification_token_bad_signature():
    ts1 = TokenService('secret-a')
    ts2 = TokenService('secret-b')
    token = ts1.generate_verification_token('user@example.com')
    assert ts2.validate_verification_token(token) is None
```

- Create two instances with different secrets
- Generate token with first, validate with second
- Assert returns `None` (invalid token)

**Mocking SMTP Context Manager:**

Pattern from `tests/test_email.py:19-38`:
```python
with patch('ecotone_common.email.smtplib.SMTP') as mock_smtp:
    ctx = MagicMock()
    mock_smtp.return_value.__enter__ = MagicMock(return_value=ctx)
    mock_smtp.return_value.__exit__ = MagicMock(return_value=False)
    result = backend.send('to@example.com', 'Subject', '<p>Body</p>')
```

- Patch the SMTP class
- Mock context manager entry/exit
- Assert methods called on context: `ctx.starttls.assert_called_once()`, `ctx.sendmail.assert_called_once()`

**Mocking Function Return Values:**

Pattern from `tests/test_consent.py:23-28`:
```python
def test_get_current_eula_version_dict_cursor():
    cursor = MagicMock()
    cursor.fetchone.return_value = {'version': '2.1'}
    result = get_current_eula_version(cursor)
    assert result == '2.1'
    cursor.execute.assert_called_once()
```

- Create mock object
- Set return value for method: `cursor.fetchone.return_value = {'version': '2.1'}`
- Call function with mock
- Assert both result and method call

**Factory Pattern Testing:**

Pattern from `tests/test_email.py:59-78`:
```python
def test_create_email_backend_sendgrid():
    backend = create_email_backend({'SENDGRID_API_KEY': 'sg-key', 'FROM_EMAIL': 'a@b.com'})
    assert isinstance(backend, SendGridBackend)
    assert backend.api_key == 'sg-key'

def test_create_email_backend_smtp():
    backend = create_email_backend({
        'SMTP_HOST': 'smtp.gmail.com',
        'SMTP_PORT': '587',
        'SMTP_USERNAME': 'user',
        'SMTP_PASSWORD': 'pass',
    })
    assert isinstance(backend, SmtpBackend)
    assert backend.host == 'smtp.gmail.com'

def test_create_email_backend_log_fallback():
    backend = create_email_backend({})
    assert isinstance(backend, LogBackend)
```

- Test factory logic with different config inputs
- Assert correct backend class instantiated
- Verify configuration passed correctly
- Test fallback behavior (empty config → LogBackend)

## Logging in Tests

**Using caplog fixture:**

Pattern from `tests/test_email.py:10-16`:
```python
def test_log_backend(caplog):
    backend = LogBackend()
    with caplog.at_level(logging.INFO):
        result = backend.send('test@example.com', 'Hello', '<b>Hi</b>')
    assert result is True
    assert 'test@example.com' in caplog.text
    assert 'Hello' in caplog.text
```

- Use pytest's `caplog` fixture (fixture injected automatically)
- Set log level: `caplog.at_level(logging.INFO)`
- Call function that logs
- Assert logged messages: `assert 'text' in caplog.text`

---

*Testing analysis: 2026-02-10*
