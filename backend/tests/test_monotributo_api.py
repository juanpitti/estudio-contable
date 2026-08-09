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
    c.post("/clientes", json={"cuit": "20-27396523-9", "razon_social": "Mono SA", "condicion_iva": "MT"})
    yield c
    app.dependency_overrides.clear()


def test_get_monotributo_cliente_existente(client):
    r = client.get("/clientes/1/monotributo")
    assert r.status_code == 200
    data = r.json()
    assert "categoria_actual" in data
    assert "porcentaje_del_techo" in data


def test_get_monotributo_cliente_inexistente_404(client):
    r = client.get("/clientes/999/monotributo")
    assert r.status_code == 404
