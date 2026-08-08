"""Tipos del pipeline de extracción (Plan 1 del v3 / Etapa 1 del v4)."""

from dataclasses import dataclass, field
from typing import Any, Literal

Fuente = Literal["qr", "ocr", "llm"]

# Por debajo de este umbral el campo se marca para revisión humana.
UMBRAL_CONFIANZA = 0.85


@dataclass(frozen=True)
class CampoExtraido:
    valor: Any
    confianza: float
    fuente: Fuente


@dataclass(frozen=True)
class ResultadoExtraccion:
    campos: dict[str, CampoExtraido] = field(default_factory=dict)
    estado: Literal["ok", "revisar"] = "revisar"
