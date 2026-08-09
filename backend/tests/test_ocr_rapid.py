import pytest

from app.extractor.ocr_rapid import (
    RapidOcrExtractor,
    _extraer_cae,
    _extraer_cuit,
    _extraer_fecha,
    _extraer_importe,
    _extraer_nro,
    _extraer_pto_vta,
    _extraer_tipo,
)


# ── Tests unitarios de regex ──

class TestRegexExtractors:
    def test_extraer_cuit_ok(self):
        assert _extraer_cuit("CUIT: 30-12345678-1") == ("30-12345678-1", 0.95)
        assert _extraer_cuit("CUIT 30123456781") == ("30-12345678-1", 0.95)

    def test_extraer_cuit_invalido(self):
        # CUIT con dígito verificador incorrecto
        assert _extraer_cuit("CUIT: 30-12345678-0") is None
        assert _extraer_cuit("CUIT: 30-12345678-9") is None

    def test_extraer_fecha(self):
        assert _extraer_fecha("Fecha: 15/03/2026") == ("15/03/2026", 0.90)
        assert _extraer_fecha("Fecha 15-03-26") == ("15/03/2026", 0.90)

    def test_extraer_importe(self):
        valor, conf = _extraer_importe("Total: $12.500,00")
        assert valor == 12500.0
        assert conf == 0.85

    def test_extraer_importe_con_punto_decimal(self):
        valor, conf = _extraer_importe("Total: $12500.50")
        assert valor == 12500.5

    def test_extraer_tipo(self):
        assert _extraer_tipo("Factura A") == (1, 0.90)
        assert _extraer_tipo("FACTURA B") == (6, 0.90)
        assert _extraer_tipo("Factura C") == (11, 0.90)
        assert _extraer_tipo("Nota de Débito") is None

    def test_extraer_nro(self):
        assert _extraer_nro("N° 12345678") == (12345678, 0.85)
        assert _extraer_nro("Comp. 00001234") == (1234, 0.85)

    def test_extraer_pto_vta(self):
        assert _extraer_pto_vta("Punto de Venta: 00002") == (2, 0.85)
        assert _extraer_pto_vta("PV: 12345") == (12345, 0.85)

    def test_extraer_cae(self):
        assert _extraer_cae("CAE: 12345678901234") == ("12345678901234", 0.95)


# ── Tests de integración con imagen generada ──

class TestRapidOcrExtractor:
    @pytest.fixture(scope="class")
    def extractor(self):
        try:
            return RapidOcrExtractor()
        except Exception as e:
            pytest.skip(f"RapidOCR no disponible: {e}")

    @pytest.fixture
    def imagen_factura(self):
        from io import BytesIO
        from PIL import Image, ImageDraw, ImageFont

        img = Image.new("RGB", (800, 400), "white")
        draw = ImageDraw.Draw(img)
        font = ImageFont.load_default()

        draw.text((50, 50), "CUIT: 30-12345678-1", fill="black", font=font)
        draw.text((50, 100), "Tipo: 01 Factura A", fill="black", font=font)
        draw.text((50, 150), "Fecha: 15/03/2026", fill="black", font=font)
        draw.text((50, 200), "Importe: $12.500,00", fill="black", font=font)

        buf = BytesIO()
        img.save(buf, format="PNG")
        return buf.getvalue()

    def test_extrae_cuit(self, extractor, imagen_factura):
        campos = extractor.extraer(imagen_factura)
        assert "cuit" in campos
        assert campos["cuit"].valor == "30-12345678-1"
        assert campos["cuit"].fuente == "ocr"
        assert campos["cuit"].confianza > 0.7

    def test_extrae_fecha(self, extractor, imagen_factura):
        campos = extractor.extraer(imagen_factura)
        assert "fecha" in campos
        assert campos["fecha"].valor == "15/03/2026"

    def test_extrae_importe(self, extractor, imagen_factura):
        campos = extractor.extraer(imagen_factura)
        assert "importe" in campos
        assert campos["importe"].valor == 12500.0

    def test_extrae_tipo(self, extractor, imagen_factura):
        campos = extractor.extraer(imagen_factura)
        assert "tipo" in campos
        assert campos["tipo"].valor == 1  # Factura A

    def test_imagen_vacia(self, extractor):
        from io import BytesIO
        from PIL import Image

        img = Image.new("RGB", (100, 100), "white")
        buf = BytesIO()
        img.save(buf, format="PNG")
        campos = extractor.extraer(buf.getvalue())
        assert campos == {}
