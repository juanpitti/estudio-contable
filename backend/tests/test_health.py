from fastapi.testclient import TestClient

from app.main import app


def test_health_devuelve_ok_y_version():
    r = TestClient(app).get("/health")
    assert r.status_code == 200
    body = r.json()
    assert body["status"] == "ok"
    assert body["env"] in ("homologacion", "produccion")
