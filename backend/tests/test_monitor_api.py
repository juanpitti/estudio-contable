import pytest
from fastapi.testclient import TestClient

from app.api.clientes import RepoClientes, get_repo
from app.main import app


@pytest.fixture
def client():
    repo = RepoClientes()
    app.dependency_overrides[get_repo] = lambda: repo
    c = TestClient(app)
    token = c.post("/auth/login", json={"username": "owner", "password": "owner123"}).json()["access_token"]
    c.headers["Authorization"] = f"Bearer {token}"
    c.post("/clientes", json={"cuit": "20-27396523-9", "razon_social": "Monitor SA", "condicion_iva": "RI"})
    yield c
    app.dependency_overrides.clear()


def test_get_monitor(client):
    r = client.get("/monitor")
    assert r.status_code == 200
    data = r.json()
    assert "alertas" in data
    assert "resumen" in data


def test_get_monitor_alertas_es_array(client):
    r = client.get("/monitor")
    assert isinstance(r.json()["alertas"], list)
