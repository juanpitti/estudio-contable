"""Tests del lector de QR AFIP — formato real fe/qr/?p=base64(json)."""

import base64
import io
import json

import qrcode

from app.extractor.qr import extraer_qr

PAYLOAD_AFIP = {
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


def _png_qr(contenido: str) -> bytes:
    img = qrcode.make(contenido)
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue()


def qr_afip_png(payload: dict | None = None) -> bytes:
    p = base64.b64encode(json.dumps(payload or PAYLOAD_AFIP).encode()).decode()
    return _png_qr(f"https://www.afip.gob.ar/fe/qr/?p={p}")


def test_extraer_qr_devuelve_payload_afip():
    datos = extraer_qr(qr_afip_png())
    assert datos is not None
    assert datos["cuit"] == 20273965239
    assert datos["codAut"] == 75321098765432
    assert datos["importe"] == 1210.5


def test_extraer_qr_imagen_sin_qr_devuelve_none():
    png = io.BytesIO()
    qrcode.constants  # noqa — asegura import
    from PIL import Image

    Image.new("RGB", (64, 64), "white").save(png, format="PNG")
    assert extraer_qr(png.getvalue()) is None


def test_extraer_qr_contenido_no_afip_devuelve_none():
    assert extraer_qr(_png_qr("hola, no soy un QR fiscal")) is None
