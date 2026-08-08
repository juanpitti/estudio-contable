"""Comprobante a efectos de IVA (venta o compra) con líneas por alícuota.

Todo comprobante ingresa por confirmación humana (bitácora, Ley 20.488):
`confirmado_por` y `confirmado_en` son obligatorios en la ingesta.
"""

from dataclasses import dataclass
from datetime import date, datetime
from decimal import Decimal
from typing import Literal


@dataclass(frozen=True)
class AlicuotaLinea:
    alicuota: Decimal  # 0.21, 0.105, 0.27
    neto: Decimal
    iva: Decimal


@dataclass(frozen=True)
class ComprobanteIva:
    id: int
    cliente_id: int
    tipo: Literal["venta", "compra"]
    fecha: date
    lineas: list[AlicuotaLinea]
    confirmado_por: str
    confirmado_en: datetime | None

    @property
    def periodo(self) -> str:
        """Período de liquidación YYYY-MM."""
        return self.fecha.strftime("%Y-%m")

    @property
    def total_iva(self) -> Decimal:
        return sum((l.iva for l in self.lineas), Decimal("0"))
