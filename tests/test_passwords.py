"""Tests for ecotone_common.passwords."""

from ecotone_common.passwords import check_password, hash_password, validate_strength


def test_hash_and_check():
    hashed = hash_password("MySecret123")
    assert check_password("MySecret123", hashed)
    assert not check_password("WrongPassword", hashed)


def test_hash_returns_string():
    hashed = hash_password("test")
    assert isinstance(hashed, str)
    assert hashed.startswith("$2b$")


def test_different_passwords_different_hashes():
    h1 = hash_password("password1")
    h2 = hash_password("password1")
    # bcrypt generates different salts each time
    assert h1 != h2
    # But both should verify
    assert check_password("password1", h1)
    assert check_password("password1", h2)


def test_validate_strength_valid():
    assert validate_strength("Abcdef1x") == []


def test_validate_strength_too_short():
    errors = validate_strength("Ab1")
    assert any("8 characters" in e for e in errors)


def test_validate_strength_no_upper():
    errors = validate_strength("abcdefg1")
    assert any("uppercase" in e for e in errors)


def test_validate_strength_no_lower():
    errors = validate_strength("ABCDEFG1")
    assert any("lowercase" in e for e in errors)


def test_validate_strength_no_digit():
    errors = validate_strength("Abcdefgh")
    assert any("digit" in e for e in errors)


def test_validate_strength_custom_min_length():
    errors = validate_strength("Ab1xxxxx", min_length=12)
    assert any("12 characters" in e for e in errors)


def test_validate_strength_relaxed():
    errors = validate_strength(
        "short", min_length=3, require_upper=False, require_lower=False, require_digit=False
    )
    assert errors == []
