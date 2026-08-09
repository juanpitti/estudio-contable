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
    c.post("/clientes", json={"cuit": "20-27396523-9", "razon_social": "Conv SA", "condicion_iva": "RI"})
    yield c
    app.dependency_overrides.clear()


def test_post_convenio_atribucion(client):
    r = client.post("/clientes/1/convenio/cm05", json={
        "ingresos": {"01": "600000", "02": "400000"},
    })
    assert r.status_code == 200
    data = r.json()
    assert data["total_ingresos"] == "1000000"
    assert data["atribuciones"]["01"]["porcentaje"] == "60.00"


def test_post_convenio_cliente_inexistente_404(client):
    r = client.post("/clientes/999/convenio/cm05", json={"ingresos": {}})
    assert r.status_code == 404
