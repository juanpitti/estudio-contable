"""Extractor OCR usando RapidOCR (onnxruntime).

Lee texto plano de imágenes de facturas y extrae campos con regex.
Confianza ponderada por: (1) confianza OCR del motor y (2) match estricto del patrón.
"""

import re
from decimal import Decimal

from app.cuit import formatear_cuit
from app.extractor.ocr import ExtractorOcr
from app.extractor.tipos import CampoExtraido


def _texto_plano(rapidocr_result: tuple) -> str:
    """Une todas las líneas OCR en un bloque de texto."""
    lineas = rapidocr_result[0] if rapidocr_result and len(rapidocr_result) > 0 else []
    return "\n".join(line[1] for line in lineas)


def _confianza_promedio(rapidocr_result: tuple) -> float:
    """Promedio de confianzas del motor OCR."""
    lineas = rapidocr_result[0] if rapidocr_result and len(rapidocr_result) > 0 else []
    if not lineas:
        return 0.0
    return sum(line[2] for line in lineas) / len(lineas)


# ── Patrones regex para campos típicos de facturas argentinas ──
_RE_CUIT = re.compile(r"(\d{2})[-.]?(\d{8})[-.]?(\d{1})")
_RE_FECHA = re.compile(r"(\d{1,2})[/-](\d{1,2})[/-](\d{2,4})")
_RE_IMPORTE = re.compile(r"[\$\u20AC\u00A3]?\s*([\d.]+[,\.]\d{2})")
_RE_TIPO_COMP = re.compile(r"Factura\s+([ABC])(?:\s+\D|$)", re.IGNORECASE)
_RE_NUMERO_COMP = re.compile(r"(?:N[°ºo]|Comp\.?|Nro)[\s.:]*(\d{4,8})", re.IGNORECASE)
_RE_PTO_VTA = re.compile(r"(?:Punto\s+de\s+Venta|P\.?V\.?)[\s.:]*(\d{1,5})", re.IGNORECASE)
_RE_CAE = re.compile(r"CAE[\s.:]*(\d{14})")


def _extraer_cuit(texto: str) -> tuple[str, float] | None:
    m = _RE_CUIT.search(texto)
    if not m:
        return None
    crudo = f"{m.group(1)}{m.group(2)}{m.group(3)}"
    try:
        return formatear_cuit(crudo), 0.95
    except ValueError:
        return None


def _extraer_fecha(texto: str) -> tuple[str, float] | None:
    m = _RE_FECHA.search(texto)
    if not m:
        return None
    dd, mm, aaaa = m.group(1), m.group(2), m.group(3)
    if len(aaaa) == 2:
        año_int = int(aaaa)
        aaaa = f"20{aaaa}" if año_int < 50 else f"19{aaaa}"
    return f"{int(dd):02d}/{int(mm):02d}/{aaaa}", 0.90


def _extraer_importe(texto: str) -> tuple[float, float] | None:
    # Tomamos el mayor importe numérico (el total suele ser el más grande)
    matches = _RE_IMPORTE.findall(texto)
    if not matches:
        return None
    valores: list[float] = []
    for m in matches:
        # Decide si el separador decimal es coma o punto
        raw = m.strip()
        if "," in raw and "." in raw:
            # 1.234,56  → punto es miles, coma decimal
            raw = raw.replace(".", "").replace(",", ".")
        elif "," in raw:
            raw = raw.replace(",", ".")
        try:
            valores.append(float(raw))
        except ValueError:
            continue
    if not valores:
        return None
    return max(valores), 0.85


def _extraer_tipo(texto: str) -> tuple[int, float] | None:
    m = _RE_TIPO_COMP.search(texto)
    if not m:
        return None
    letra = m.group(1).upper()
    mapping = {"A": 1, "B": 6, "C": 11, "M": 51}
    return mapping.get(letra, 0), 0.90


def _extraer_nro(texto: str) -> tuple[int, float] | None:
    m = _RE_NUMERO_COMP.search(texto)
    if not m:
        return None
    return int(m.group(1)), 0.85


def _extraer_pto_vta(texto: str) -> tuple[int, float] | None:
    m = _RE_PTO_VTA.search(texto)
    if not m:
        return None
    return int(m.group(1)), 0.85


def _extraer_cae(texto: str) -> tuple[str, float] | None:
    m = _RE_CAE.search(texto)
    if not m:
        return None
    return m.group(1), 0.95


class RapidOcrExtractor:
    """Implementación real de ExtractorOcr usando RapidOCR + regex."""

    def __init__(self) -> None:
        from rapidocr_onnxruntime import RapidOCR
        self._engine = RapidOCR()

    def extraer(self, imagen: bytes) -> dict[str, CampoExtraido]:
        result = self._engine(imagen)
        if not result or not result[0]:
            return {}

        texto = _texto_plano(result)
        conf_base = _confianza_promedio(result)
        campos: dict[str, CampoExtraido] = {}

        def add(nombre: str, extractor) -> None:
            res = extractor(texto)
            if res:
                valor, conf_patron = res
                # Confianza final = promedio entre confianza OCR y confianza del patrón regex
                conf_final = round((conf_base + conf_patron) / 2, 3)
                campos[nombre] = CampoExtraido(valor, conf_final, "ocr")

        add("cuit", _extraer_cuit)
        add("fecha", _extraer_fecha)
        add("importe", _extraer_importe)
        add("tipo", _extraer_tipo)
        add("nro", _extraer_nro)
        add("pto_vta", _extraer_pto_vta)
        add("cae", _extraer_cae)

        return campos




