import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.api.clientes import RepoClientes, get_repo
from app.main import app


@pytest.fixture
def client(db_session: Session):
    repo = RepoClientes(db_session)
    app.dependency_overrides[get_repo] = lambda: repo
    c = TestClient(app)
    token = c.post("/auth/login", json={"username": "owner", "password": "owner123"}).json()["access_token"]
    c.headers["Authorization"] = f"Bearer {token}"
    c.post("/clientes", json={"cuit": "20-27396523-9", "razon_social": "Dash SA", "condicion_iva": "RI"})
    yield c
    app.dependency_overrides.clear()


def test_dashboard_devuelve_clientes(client):
    r = client.get("/dashboard")
    assert r.status_code == 200
    data = r.json()
    assert "clientes" in data
    assert len(data["clientes"]) == 1


def test_dashboard_tiene_vencimientos(client):
    r = client.get("/dashboard")
    assert "vencimientos_proximos" in r.json()


def test_dashboard_tiene_alertas(client):
    r = client.get("/dashboard")
    assert "alertas" in r.json()
