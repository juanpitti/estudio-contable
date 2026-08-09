import pytest
from fastapi.testclient import TestClient

from app.main import app


@pytest.fixture
def client():
    c = TestClient(app)
    token = c.post("/auth/login", json={"username": "owner", "password": "owner123"}).json()["access_token"]
    c.headers["Authorization"] = f"Bearer {token}"
    yield c


def test_post_revision(client):
    r = client.post("/revisiones", json={
        "entidad_tipo": "liquidacion_iva",
        "entidad_id": 1,
        "estado": "aprobado",
        "comentario": "OK",
    })
    assert r.status_code == 201
    data = r.json()
    assert data["estado"] == "aprobado"


def test_get_revisiones(client):
    client.post("/revisiones", json={
        "entidad_tipo": "liquidacion_iva",
        "entidad_id": 2,
        "estado": "revisado",
        "comentario": "",
    })
    r = client.get("/revisiones/liquidacion_iva/2")
    assert r.status_code == 200
    assert len(r.json()) == 1
