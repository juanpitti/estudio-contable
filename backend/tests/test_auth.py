import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.api.clientes import RepoClientes, get_repo
from app.main import app


@pytest.fixture
def client(db_session: Session):
    repo = RepoClientes(db_session)
    app.dependency_overrides[get_repo] = lambda: repo
    yield TestClient(app)
    app.dependency_overrides.clear()


def _token(client, username="owner", password="owner123"):
    return client.post(
        "/auth/login", json={"username": username, "password": password}
    ).json()["access_token"]


def test_login_ok_devuelve_token(client):
    r = client.post("/auth/login", json={"username": "owner", "password": "owner123"})
    assert r.status_code == 200
    assert r.json()["token_type"] == "bearer"
    assert r.json()["access_token"]


def test_login_password_incorrecta_401(client):
    r = client.post("/auth/login", json={"username": "owner", "password": "mal"})
    assert r.status_code == 401


def test_login_usuario_inexistente_401(client):
    r = client.post("/auth/login", json={"username": "nadie", "password": "x"})
    assert r.status_code == 401


def test_crear_cliente_sin_token_401(client):
    r = client.post(
        "/clientes",
        json={"cuit": "20-27396523-9", "razon_social": "Prueba SA", "condicion_iva": "RI"},
    )
    assert r.status_code == 401


def test_crear_cliente_con_token_owner_201(client):
    r = client.post(
        "/clientes",
        json={"cuit": "20-11111111-2", "razon_social": "Prueba SA", "condicion_iva": "RI"},
        headers={"Authorization": f"Bearer {_token(client)}"},
    )
    assert r.status_code == 201
    r = client.post(
        "/clientes",
        json={"cuit": "20-27396523-9", "razon_social": "Prueba SA", "condicion_iva": "RI"},
        headers={"Authorization": f"Bearer {_token(client)}"},
    )
    assert r.status_code == 201
    r = client.post(
        "/clientes",
        json={"cuit": "20-11111111-2", "razon_social": "Prueba SA", "condicion_iva": "RI"},
        headers={"Authorization": f"Bearer {_token(client)}"},
    )
    assert r.status_code == 409  # CUIT duplicado


def test_token_adulterado_401(client):
    r = client.get("/clientes", headers={"Authorization": "Bearer token-falso"})
    assert r.status_code == 401


def test_rol_senior_tambien_puede_crear(client):
    r = client.post(
        "/clientes",
        json={"cuit": "20-22222222-3", "razon_social": "Prueba SA", "condicion_iva": "RI"},
        headers={"Authorization": f"Bearer {_token(client, 'senior', 'senior123')}"},
    )
    assert r.status_code == 201
    r = client.post(
        "/clientes",
        json={"cuit": "20-27396523-9", "razon_social": "Prueba SA", "condicion_iva": "RI"},
        headers={"Authorization": f"Bearer {_token(client, 'senior', 'senior123')}"},
    )
    assert r.status_code == 201
    r = client.post(
        "/clientes",
        json={"cuit": "20-22222222-3", "razon_social": "Prueba SA", "condicion_iva": "RI"},
        headers={"Authorization": f"Bearer {_token(client, 'senior', 'senior123')}"},
    )
    assert r.status_code == 409  # CUIT duplicado
