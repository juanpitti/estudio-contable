"""Tests del pipeline de extracción — criterios de aceptación del Plan v4:
QR legible → confianza 1.0 sin OCR; factura ilegible → "revisar", no inventa.
"""

import base64
import io
import json

import qrcode
from PIL import Image

from app.extractor.pipeline import PipelineExtraccion
from app.extractor.tipos import CampoExtraido, UMBRAL_CONFIANZA

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


def _qr_png(payload: dict) -> bytes:
    p = base64.b64encode(json.dumps(payload).encode()).decode()
    buf = io.BytesIO()
    qrcode.make(f"https://www.afip.gob.ar/fe/qr/?p={p}").save(buf, format="PNG")
    return buf.getvalue()


def _imagen_sin_qr() -> bytes:
    buf = io.BytesIO()
    Image.new("RGB", (64, 64), "white").save(buf, format="PNG")
    return buf.getvalue()


class OcrFake:
    """OCR de mentira que devuelve campos con baja confianza."""

    def extraer(self, imagen: bytes) -> dict[str, CampoExtraido]:
        return {
            "cuit": CampoExtraido("20-27396523-9", 0.60, "ocr"),
            "importe": CampoExtraido(1210.5, 0.40, "ocr"),
        }


def test_qr_legible_confianza_total_sin_ocr():
    r = PipelineExtraccion().procesar(_qr_png(PAYLOAD))
    assert r.estado == "ok"
    assert r.campos["cuit"].valor == "20-27396523-9"
    assert r.campos["cuit"].confianza == 1.0
    assert r.campos["cuit"].fuente == "qr"
    assert r.campos["cae"].valor == "75321098765432"
    assert r.campos["cae"].fuente == "qr"
    assert r.campos["importe"].valor == 1210.5
    assert r.campos["tipo"].valor == 6
    assert r.campos["fecha"].valor == "2026-08-01"


def test_imagen_sin_qr_cae_a_ocr_y_marca_revisar():
    r = PipelineExtraccion().procesar(_imagen_sin_qr())
    assert r.estado == "revisar"
    assert r.campos == {}  # stub OCR no inventa nada


def test_ocr_baja_confianza_marca_revisar():
    r = PipelineExtraccion(ocr=OcrFake()).procesar(_imagen_sin_qr())
    assert r.estado == "revisar"
    assert r.campos["cuit"].valor == "20-27396523-9"  # muestra lo leído
    assert r.campos["cuit"].confianza < UMBRAL_CONFIANZA


def test_qr_con_cuit_invalido_baja_confianza():
    payload = {**PAYLOAD, "cuit": 20273965230}  # dígito verificador mal
    r = PipelineExtraccion().procesar(_qr_png(payload))
    assert r.estado == "revisar"
    assert r.campos["cuit"].confianza < UMBRAL_CONFIANZA
