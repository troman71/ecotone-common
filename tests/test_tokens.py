"""Tests for ecotone_common.tokens."""

import time

from ecotone_common.tokens import TokenService


def test_verification_token_roundtrip():
    ts = TokenService("test-secret")
    token = ts.generate_verification_token("user@example.com")
    assert ts.validate_verification_token(token) == "user@example.com"


def test_verification_token_expired():
    ts = TokenService("test-secret")
    token = ts.generate_verification_token("user@example.com")
    time.sleep(2)
    assert ts.validate_verification_token(token, max_age=1) is None


def test_verification_token_bad_signature():
    ts1 = TokenService("secret-a")
    ts2 = TokenService("secret-b")
    token = ts1.generate_verification_token("user@example.com")
    assert ts2.validate_verification_token(token) is None


def test_reset_token_roundtrip():
    ts = TokenService("test-secret")
    token = ts.generate_reset_token("user@example.com")
    assert ts.validate_reset_token(token) == "user@example.com"


def test_reset_token_expired():
    ts = TokenService("test-secret")
    token = ts.generate_reset_token("user@example.com")
    time.sleep(2)
    assert ts.validate_reset_token(token, max_age=1) is None


def test_approval_token_roundtrip():
    ts = TokenService("test-secret")
    token = ts.generate_approval_token("user-123", "approve")
    data = ts.validate_approval_token(token)
    assert data["user_id"] == "user-123"
    assert data["action"] == "approve"


def test_approval_token_reject():
    ts = TokenService("test-secret")
    token = ts.generate_approval_token("user-456", "reject")
    data = ts.validate_approval_token(token)
    assert data["action"] == "reject"


def test_generic_token_roundtrip():
    ts = TokenService("test-secret")
    token = ts.generate_token({"foo": "bar", "n": 42}, salt="custom")
    data = ts.validate_token(token, salt="custom")
    assert data == {"foo": "bar", "n": 42}


def test_generic_token_wrong_salt():
    ts = TokenService("test-secret")
    token = ts.generate_token({"foo": "bar"}, salt="salt-a")
    assert ts.validate_token(token, salt="salt-b") is None


def test_invite_token_format():
    token = TokenService.generate_invite_token()
    assert isinstance(token, str)
    assert len(token) > 20


def test_invite_token_validate():
    token = TokenService.generate_invite_token()
    assert TokenService.validate_invite_token(token) is True
    assert TokenService.validate_invite_token("") is False
    assert TokenService.validate_invite_token(None) is False
