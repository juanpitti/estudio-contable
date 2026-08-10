import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.api.clientes import RepoClientes, get_repo
from app.api.comprobantes import RepoComprobantes, get_repo_comprobantes
from app.main import app


@pytest.fixture
def client(db_session: Session):
    repo_cli = RepoClientes(db_session)
    repo_comp = RepoComprobantes(db_session)
    app.dependency_overrides[get_repo] = lambda: repo_cli
    app.dependency_overrides[get_repo_comprobantes] = lambda: repo_comp
    c = TestClient(app)
    token = c.post(
        "/auth/login", json={"username": "owner", "password": "owner123"}
    ).json()["access_token"]
    c.headers["Authorization"] = f"Bearer {token}"
    c.post(
        "/clientes",
        json={"cuit": "20-27396523-9", "razon_social": "Prueba SA", "condicion_iva": "RI"},
    )
    yield c
    app.dependency_overrides.clear()


def test_descargar_arca_stub_501(client):
    r = client.post("/clientes/1/arca/descargar", json={
        "cert_path": "/fake/cert.pem",
        "key_path": "/fake/key.pem",
        "pto_vta": 1,
    })
    assert r.status_code == 501
    assert "certificado" in r.json()["detail"].lower()


def test_descargar_arca_cliente_inexistente_404(client):
    r = client.post("/clientes/999/arca/descargar", json={
        "cert_path": "/fake/cert.pem",
        "key_path": "/fake/key.pem",
        "pto_vta": 1,
    })
    assert r.status_code == 404
