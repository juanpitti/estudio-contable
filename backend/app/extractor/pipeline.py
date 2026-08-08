"""Pipeline de extracción Plan 1: detector de tipo → QR → OCR → (LLM a futuro).

Regla del Plan v4: si la confianza es baja, el sistema dice "revisar";
nunca inventa un dato.
"""

from app.extractor.normalizador import normalizar_qr
from app.extractor.ocr import ExtractorOcr, OcrNoDisponible
from app.extractor.qr import extraer_qr
from app.extractor.tipos import UMBRAL_CONFIANZA, ResultadoExtraccion


class PipelineExtraccion:
    def __init__(self, ocr: ExtractorOcr | None = None) -> None:
        self._ocr = ocr or OcrNoDisponible()

    def procesar(self, archivo: bytes) -> ResultadoExtraccion:
        payload_qr = extraer_qr(archivo)
        if payload_qr is not None:
            campos = normalizar_qr(payload_qr)
        else:
            campos = self._ocr.extraer(archivo)

        if campos and all(c.confianza >= UMBRAL_CONFIANZA for c in campos.values()):
            return ResultadoExtraccion(campos=campos, estado="ok")
        return ResultadoExtraccion(campos=campos, estado="revisar")
