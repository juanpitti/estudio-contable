import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.api.clientes import RepoClientes, get_repo
from app.api.comprobantes import RepoComprobantes, get_repo_comprobantes
from app.database import Base, get_db
from app.main import app


@pytest.fixture
def client():
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    Base.metadata.create_all(bind=engine)

    db = TestingSessionLocal()
    repo_cli = RepoClientes(db)
    repo_comp = RepoComprobantes(db)

    def override_get_db():
        try:
            yield db
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db
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
    db.close()


VENTA = {
    "tipo": "venta",
    "fecha": "2026-08-15",
    "lineas": [{"alicuota": "0.21", "neto": "100000", "iva": "21000"}],
}
COMPRA = {
    "tipo": "compra",
    "fecha": "2026-08-20",
    "lineas": [{"alicuota": "0.21", "neto": "50000", "iva": "10500"}],
}


def test_ingresar_comprobante_registra_confirmacion_humana(client):
    r = client.post("/clientes/1/comprobantes", json=VENTA)
    assert r.status_code == 201
    body = r.json()
    assert body["confirmado_por"] == "owner"
    assert body["confirmado_en"] is not None
    assert body["tipo"] == "venta"


def test_ingresar_comprobante_sin_token_401():
    app.dependency_overrides.clear()
    r = TestClient(app).post("/clientes/1/comprobantes", json=VENTA)
    assert r.status_code == 401


def test_ingresar_comprobante_cliente_inexistente_404(client):
    assert client.post("/clientes/999/comprobantes", json=VENTA).status_code == 404


def test_alicuota_invalida_422(client):
    mal = {"tipo": "venta", "fecha": "2026-08-15",
           "lineas": [{"alicuota": "0.50", "neto": "100", "iva": "50"}]}
    assert client.post("/clientes/1/comprobantes", json=mal).status_code == 422


def test_liquidacion_del_periodo_con_trazabilidad(client):
    client.post("/clientes/1/comprobantes", json=VENTA)
    client.post("/clientes/1/comprobantes", json=COMPRA)
    r = client.get("/clientes/1/iva/2026-08")
    assert r.status_code == 200
    liq = r.json()
    assert liq["debito"] == {"0.21": "21000"}
    assert liq["credito"] == {"0.21": "10500"}
    assert liq["saldo_a_pagar"] == "10500"
    assert liq["saldo_a_favor_final"] == "0"
    assert sorted(liq["comprobantes_incluidos"]) == [1, 2]


def test_liquidacion_filtra_por_periodo(client):
    client.post("/clientes/1/comprobantes", json=VENTA)  # 2026-08
    julio = {**VENTA, "fecha": "2026-07-10"}
    client.post("/clientes/1/comprobantes", json=julio)
    liq = client.get("/clientes/1/iva/2026-08").json()
    assert liq["debito"] == {"0.21": "21000"}  # solo la de agosto
    assert liq["comprobantes_incluidos"] == [1]


def test_liquidacion_con_saldo_favor_anterior(client):
    client.post("/clientes/1/comprobantes", json=VENTA)
    client.post("/clientes/1/comprobantes", json=COMPRA)
    liq = client.get("/clientes/1/iva/2026-08?saldo_favor_anterior=5000").json()
    assert liq["saldo_a_pagar"] == "5500"


def test_listar_comprobantes(client):
    client.post("/clientes/1/comprobantes", json=VENTA)
    r = client.get("/clientes/1/comprobantes")
    assert r.status_code == 200
    assert len(r.json()) == 1


def test_liquidacion_con_alerta_salto_credito(client):
    client.post("/clientes/1/comprobantes", json={
        "tipo": "venta", "fecha": "2026-08-01",
        "lineas": [{"alicuota": "0.21", "neto": "100000", "iva": "21000"}]
    })
    client.post("/clientes/1/comprobantes", json={
        "tipo": "compra", "fecha": "2026-08-01",
        "lineas": [{"alicuota": "0.21", "neto": "238095", "iva": "50000"}]
    })
    r = client.get("/clientes/1/iva/2026-08")
    assert r.status_code == 200
    data = r.json()
    assert any(a["codigo"] == "salto_credito_fiscal" for a in data["alertas"])
    assert data["saldo_a_favor_final"] == "29000"
