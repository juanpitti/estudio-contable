import pytest
from unittest.mock import patch
from fastapi.testclient import TestClient

from app.api.clientes import RepoClientes, get_repo
from app.api.comprobantes import RepoComprobantes, get_repo_comprobantes
from app.main import app


@pytest.fixture
def client():
    repo_cli = RepoClientes()
    repo_comp = RepoComprobantes()
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


def test_emitir_factura_b_exitosa(client):
    mock_wsfe = type("MockWsfe", (), {
        "fecae_solicitar": lambda self, **kw: {
            "CAE": "12345678901234", "CAEFchVto": "20260818",
            "CbteDesde": 1, "Resultado": "A",
        }
    })()
    with patch("app.api.facturacion._crear_wsfe_client", return_value=mock_wsfe):
        r = client.post("/clientes/1/facturacion/emitir", json={
            "tipo": "FACTURA_B",
            "punto_venta": 1,
            "numero": 0,
            "fecha": "2026-08-08",
            "receptor_cuit": "20345678901",
            "receptor_razon": "Cliente Test",
            "receptor_condicion": "RI",
            "neto": "10000",
            "alicuota": "0.21",
            "total": "12100",
        })
        assert r.status_code == 201
        data = r.json()
        assert data["cae"] == "12345678901234"
        assert data["numero"] == 1


def test_emitir_factura_cliente_inexistente_404(client):
    r = client.post("/clientes/999/facturacion/emitir", json={
        "tipo": "FACTURA_B",
        "punto_venta": 1,
        "fecha": "2026-08-08",
        "receptor_cuit": "20345678901",
        "receptor_razon": "X",
        "receptor_condicion": "RI",
        "neto": "10000",
        "total": "12100",
    })
    assert r.status_code == 404
