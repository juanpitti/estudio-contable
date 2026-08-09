import pytest
from fastapi.testclient import TestClient

from app.main import app


@pytest.fixture
def client():
    c = TestClient(app)
    token = c.post("/auth/login", json={"username": "owner", "password": "owner123"}).json()["access_token"]
    c.headers["Authorization"] = f"Bearer {token}"
    yield c


def test_post_asistente_pregunta(client):
    r = client.post("/asistente", json={"pregunta": "cuantos clientes tengo"})
    assert r.status_code == 200
    data = r.json()
    assert "texto" in data
    assert "fuente" in data


def test_post_asistente_iva_sin_revisar(client):
    r = client.post("/asistente", json={"pregunta": "que clientes tienen la IVA sin revisar"})
    assert r.status_code == 200
    data = r.json()
    assert "texto" in data
