from fastapi.testclient import TestClient

from app.main import app


def test_health_and_home():
    c = TestClient(app)
    h = c.get("/health")
    assert h.status_code == 200
    assert h.json()["ok"] is True
    r = c.get("/")
    assert r.status_code == 200
    assert b"LINECASE" in r.content
