import pytest
from fastapi.testclient import TestClient

from app.api.clientes import RepoClientes, get_repo
from app.main import app


@pytest.fixture
def client():
    repo = RepoClientes()  # repo fresco por test: aislamiento real
    app.dependency_overrides[get_repo] = lambda: repo
    yield TestClient(app)
    app.dependency_overrides.clear()


PAYLOAD = {"cuit": "20-27396523-9", "razon_social": "Prueba SA", "condicion_iva": "RI"}


def test_crear_cliente_cuit_valido(client):
    r = client.post("/clientes", json=PAYLOAD)
    assert r.status_code == 201
    body = r.json()
    assert body["cuit"] == "20-27396523-9"
    assert body["razon_social"] == "Prueba SA"
    assert body["id"] == 1


def test_crear_cliente_normaliza_cuit_sin_guiones(client):
    r = client.post("/clientes", json={**PAYLOAD, "cuit": "20273965239"})
    assert r.status_code == 201
    assert r.json()["cuit"] == "20-27396523-9"


def test_crear_cliente_cuit_invalido_422(client):
    r = client.post("/clientes", json={**PAYLOAD, "cuit": "20-27396523-0"})
    assert r.status_code == 422


def test_crear_cliente_condicion_iva_invalida_422(client):
    r = client.post("/clientes", json={**PAYLOAD, "condicion_iva": "XX"})
    assert r.status_code == 422


def test_cuit_duplicado_409(client):
    assert client.post("/clientes", json=PAYLOAD).status_code == 201
    r = client.post("/clientes", json={**PAYLOAD, "razon_social": "Otra SA"})
    assert r.status_code == 409


def test_listar_clientes(client):
    client.post("/clientes", json=PAYLOAD)
    r = client.get("/clientes")
    assert r.status_code == 200
    assert len(r.json()) == 1


def test_obtener_cliente_inexistente_404(client):
    assert client.get("/clientes/999").status_code == 404


def test_obtener_cliente_existente(client):
    creado = client.post("/clientes", json=PAYLOAD).json()
    r = client.get(f"/clientes/{creado['id']}")
    assert r.status_code == 200
    assert r.json()["cuit"] == "20-27396523-9"
