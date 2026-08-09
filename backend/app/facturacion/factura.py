"""Modelo de factura a emitir via WSFE."""

from dataclasses import dataclass
from decimal import Decimal
from enum import Enum


class TipoComprobante(Enum):
    FACTURA_A = 1
    FACTURA_B = 6
    FACTURA_C = 11
    FACTURA_M = 51
    NOTA_CREDITO_A = 3
    NOTA_CREDITO_B = 8
    NOTA_CREDITO_C = 13
    NOTA_DEBITO_A = 2
    NOTA_DEBITO_B = 7
    NOTA_DEBITO_C = 12


@dataclass(frozen=True)
class SolicitudFactura:
    tipo: TipoComprobante
    punto_venta: int
    numero: int  # 0 para que WSFE asigne
    fecha: str  # YYYY-MM-DD
    receptor_cuit: str
    receptor_razon: str
    receptor_condicion: str  # RI, MT, EX, CF
    neto: Decimal
    iva: Decimal
    total: Decimal
    concepto: int = 1  # 1=Productos, 2=Servicios, 3=Productos y Servicios


def calcular_iva(neto: Decimal, alicuota: Decimal) -> Decimal:
    return (neto * alicuota).quantize(Decimal("0.01"))
