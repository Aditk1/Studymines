"""Smoke tests for public FastAPI endpoints that do not require external services."""

import importlib

from fastapi.testclient import TestClient


def test_root_and_health(monkeypatch):
    monkeypatch.setenv("SUPABASE_JWT_SECRET", "test-secret")
    main = importlib.import_module("app.main")
    client = TestClient(main.app)

    root = client.get("/")
    health = client.get("/health")

    assert root.status_code == 200
    assert root.json()["name"] == "master_eduRAG"
    assert health.json() == {"status": "ok"}


def test_protected_endpoint_without_token_returns_403(monkeypatch):
    monkeypatch.setenv("SUPABASE_JWT_SECRET", "test-secret")
    main = importlib.import_module("app.main")
    client = TestClient(main.app)

    response = client.get("/api/v1/users/me")

    assert response.status_code in {401, 403}
