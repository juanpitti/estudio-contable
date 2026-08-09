import pytest
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
    # Ingresar una compra
    c.post("/clientes/1/comprobantes", json={
        "tipo": "compra", "fecha": "2026-08-01",
        "lineas": [{"alicuota": "0.21", "neto": "10000", "iva": "2100"}]
    })
    yield c
    app.dependency_overrides.clear()


def test_importar_csv_y_conciliar(client):
    csv = b"fecha;descripcion;debito;\n2026-08-01;PAGO PROVEEDOR;12100,00;\n"
    r = client.post(
        "/clientes/1/conciliacion/importar",
        data={"delimitador": ";"},
        files={"archivo": ("movimientos.csv", csv, "text/csv")},
    )
    assert r.status_code == 200
    data = r.json()
    assert data["porcentaje_match"] > 0
    assert len(data["matches"]) == 1
    assert data["matches"][0]["nivel"] == "exacto"
    assert data["duplicados"] == 0


def test_conciliar_cliente_inexistente_404(client):
    csv = b"fecha;descripcion;debito;\n2026-08-01;PAGO;1000;\n"
    r = client.post(
        "/clientes/999/conciliacion/importar",
        data={"delimitador": ";"},
        files={"archivo": ("movimientos.csv", csv, "text/csv")},
    )
    assert r.status_code == 404
