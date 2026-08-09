"""Modelo de movimiento bancario importado."""

from dataclasses import dataclass
from datetime import date
from decimal import Decimal
from typing import Literal


@dataclass(frozen=True)
class MovimientoBancario:
    id: int
    cliente_id: int
    fecha: date
    descripcion: str
    monto: Decimal
    tipo: Literal["debito", "credito"]
    banco: str = ""
