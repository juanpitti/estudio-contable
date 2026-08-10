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
    c.post("/clientes", json={"cuit": "20-27396523-9", "razon_social": "F931 SA", "condicion_iva": "RI"})
    yield c
    app.dependency_overrides.clear()


def test_post_generar_f931(client):
    r = client.post("/clientes/1/f931/generar", json={
        "periodo": "202608",
        "empleados": [
            {"cuit": "20345678901", "apellido_nombre": "GARCIA JUAN", "remuneracion": "100000.00", "aportes": "17000.00", "contribuciones": "21000.00", "situacion_revista": "1"},
        ],
    })
    assert r.status_code == 200
    assert "01" in r.text
    assert "02" in r.text
    assert "03" in r.text


def test_post_generar_f931_cliente_inexistente_404(client):
    r = client.post("/clientes/999/f931/generar", json={
        "periodo": "202608",
        "empleados": [],
    })
    assert r.status_code == 404
