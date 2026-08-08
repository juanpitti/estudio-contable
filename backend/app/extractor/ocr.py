"""Interfaz del extractor OCR.

Iteración actual: stub honesto que no devuelve nada (el sistema dice
"revisar" antes que inventar). Próxima iteración: tesseract local +
fallback LLM, enchufados detrás de este Protocol sin tocar el pipeline.
"""

from typing import Protocol

from app.extractor.tipos import CampoExtraido


class ExtractorOcr(Protocol):
    def extraer(self, imagen: bytes) -> dict[str, CampoExtraido]: ...


class OcrNoDisponible:
    """Stub: OCR real aún no implementado. Devuelve vacío -> estado 'revisar'."""

    def extraer(self, imagen: bytes) -> dict[str, CampoExtraido]:
        return {}
