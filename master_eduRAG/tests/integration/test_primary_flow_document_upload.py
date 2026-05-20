"""Primary journey integration test for signup, archive upload, and dashboard retrieval."""

import importlib
import uuid
from pathlib import Path

from fastapi.testclient import TestClient


def test_signup_upload_without_analysis_and_dashboard(monkeypatch, tmp_path: Path):
    monkeypatch.setenv("SUPABASE_JWT_SECRET", "test-secret")
    monkeypatch.setenv("DATABASE_URL", f"sqlite:///{tmp_path / 'edurag.db'}")

    database = importlib.import_module("app.database")
    database = importlib.reload(database)
    main = importlib.import_module("app.main")
    main = importlib.reload(main)
    database.init_db()

    client = TestClient(main.app)

    email = f"ada-{uuid.uuid4().hex}@example.edu"
    signup = client.post(
        "/api/v1/auth/signup",
        data={
            "name": "Ada Lovelace",
            "email": email,
            "password": "password123",
            "student_level": "undergraduate",
        },
    )
    assert signup.status_code == 200
    payload = signup.json()
    token = payload["access_token"]
    user_id = payload["user"]["id"]

    upload = client.post(
        "/api/v1/upload/document",
        data={"user_id": user_id, "analyze": "false", "subject": "CS", "topic": "Testing"},
        files={"file": ("lesson.txt", b"Testing checks behavior.", "text/plain")},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert upload.status_code == 200
    assert upload.json()["is_analyzed"] is False

    dashboard = client.get("/api/v1/users/me", headers={"Authorization": f"Bearer {token}"})
    assert dashboard.status_code == 200
    assert dashboard.json()["uploads_count"] == 1
