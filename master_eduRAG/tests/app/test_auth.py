"""Tests for LMS authentication helpers."""

import importlib

import pytest


@pytest.fixture()
def auth(monkeypatch):
    """Import auth with a deterministic JWT secret."""
    monkeypatch.setenv("SUPABASE_JWT_SECRET", "test-secret")
    module = importlib.import_module("app.lms.auth")
    return importlib.reload(module)


def test_password_hash_round_trip(auth):
    hashed = auth.get_password_hash("correct horse battery staple")

    assert hashed != "correct horse battery staple"
    assert auth.verify_password("correct horse battery staple", hashed)
    assert not auth.verify_password("wrong", hashed)


def test_detect_role_from_email(auth):
    assert auth.detect_role_from_email("teacher@example.edu") == "teacher"
    assert auth.detect_role_from_email("prof.singh@example.edu") == "teacher"
    assert auth.detect_role_from_email("student@example.edu") == "student"


def test_create_access_token_contains_subject_and_audience(auth):
    token = auth.create_access_token({"sub": "user-123"})
    payload = auth._jwt_decode(token)

    assert payload["sub"] == "user-123"
    assert payload["aud"] == "authenticated"
    assert "exp" in payload
