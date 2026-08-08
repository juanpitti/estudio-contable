import base64
import io
import json

import pytest
import qrcode
from fastapi.testclient import TestClient

from app.main import app

PAYLOAD = {
    "ver": 1,
    "fecha": "2026-08-01",
    "cuit": 20273965239,
    "ptoVta": 1,
    "tipoCmp": 6,
    "nroCmp": 42,
    "importe": 1210.5,
    "moneda": "PES",
    "ctz": 1,
    "tipoDocRec": 80,
    "nroDocRec": 20987654321,
    "tipoCodAut": "E",
    "codAut": 75321098765432,
}


def _qr_png() -> bytes:
    p = base64.b64encode(json.dumps(PAYLOAD).encode()).decode()
    buf = io.BytesIO()
    qrcode.make(f"https://www.afip.gob.ar/fe/qr/?p={p}").save(buf, format="PNG")
    return buf.getvalue()


@pytest.fixture
def client():
    c = TestClient(app)
    token = c.post(
        "/auth/login", json={"username": "owner", "password": "owner123"}
    ).json()["access_token"]
    c.headers["Authorization"] = f"Bearer {token}"
    return c


def test_subir_factura_con_qr_devuelve_campos(client):
    r = client.post(
        "/extraccion/comprobante",
        files={"archivo": ("factura.png", _qr_png(), "image/png")},
    )
    assert r.status_code == 200
    body = r.json()
    assert body["estado"] == "ok"
    assert body["campos"]["cuit"]["valor"] == "20-27396523-9"
    assert body["campos"]["cuit"]["confianza"] == 1.0
    assert body["campos"]["cuit"]["fuente"] == "qr"
    assert body["campos"]["cae"]["valor"] == "75321098765432"


def test_subir_factura_sin_token_401():
    r = TestClient(app).post(
        "/extraccion/comprobante",
        files={"archivo": ("factura.png", _qr_png(), "image/png")},
    )
    assert r.status_code == 401


def test_subir_archivo_sin_qr_marca_revisar(client):
    buf = io.BytesIO()
    from PIL import Image

    Image.new("RGB", (64, 64), "white").save(buf, format="PNG")
    r = client.post(
        "/extraccion/comprobante",
        files={"archivo": ("borrosa.png", buf.getvalue(), "image/png")},
    )
    assert r.status_code == 200
    assert r.json()["estado"] == "revisar"
    assert r.json()["campos"] == {}
