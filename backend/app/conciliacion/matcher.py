"""Motor de conciliación con 4 niveles de match.

Niveles (de más estricto a más permisivo):
1. EXACTO: monto exacto + fecha exacta
2. MONTO_FECHA: monto exacto + fecha exacta (compatibilidad futura con CUIT)
3. MONTO_RANGO: monto exacto + fecha +/- 3 días
4. APROXIMADO: monto +/- 2% + fecha +/- 5 días
"""

from dataclasses import dataclass
from decimal import Decimal
from datetime import date, timedelta
from enum import Enum

from app.conciliacion.movimiento import MovimientoBancario
from app.iva.comprobante import ComprobanteIva


class NivelMatch(Enum):
    EXACTO = "exacto"
    MONTO_FECHA = "monto_fecha"
    MONTO_RANGO = "monto_rango"
    APROXIMADO = "aproximado"


@dataclass(frozen=True)
class Match:
    comprobante_id: int
    movimiento_id: int
    nivel: NivelMatch
    monto_comprobante: Decimal
    monto_movimiento: Decimal


@dataclass(frozen=True)
class Diferencia:
    comprobante_id: int
    movimiento_id: int
    monto_comprobante: Decimal
    monto_movimiento: Decimal
    monto_diferencia: Decimal


@dataclass(frozen=True)
class ResultadoConciliacion:
    matches: list[Match]
    sin_match_compras: list[ComprobanteIva]
    sin_match_banco: list[MovimientoBancario]
    diferencias: list[Diferencia]
    porcentaje_match: float


def _total_comprobante(c: ComprobanteIva) -> Decimal:
    """Importe total del comprobante (neto + iva)."""
    return sum(l.neto + l.iva for l in c.lineas)


def _monto_igual(a: Decimal, b: Decimal) -> bool:
    return a == b


def _monto_aproximado(a: Decimal, b: Decimal, tolerancia: Decimal = Decimal("0.02")) -> bool:
    if a == 0:
        return False
    diff = abs(a - b) / a
    return diff <= tolerancia


def conciliar(
    compras: list[ComprobanteIva],
    movimientos: list[MovimientoBancario],
) -> ResultadoConciliacion:
    matches: list[Match] = []
    diferencias: list[Diferencia] = []
    compras_pendientes = list(compras)
    movs_pendientes = list(movimientos)

    # Nivel 1: Exacto (monto exacto + fecha exacta)
    for c in list(compras_pendientes):
        total = _total_comprobante(c)
        for m in list(movs_pendientes):
            if _monto_igual(total, m.monto) and c.fecha == m.fecha:
                matches.append(Match(c.id, m.id, NivelMatch.EXACTO, total, m.monto))
                compras_pendientes.remove(c)
                movs_pendientes.remove(m)
                break

    # Nivel 2: Monto + fecha exacta
    for c in list(compras_pendientes):
        total = _total_comprobante(c)
        for m in list(movs_pendientes):
            if _monto_igual(total, m.monto) and c.fecha == m.fecha:
                matches.append(Match(c.id, m.id, NivelMatch.MONTO_FECHA, total, m.monto))
                compras_pendientes.remove(c)
                movs_pendientes.remove(m)
                break

    # Nivel 3: Monto exacto + fecha +/- 3 días
    for c in list(compras_pendientes):
        total = _total_comprobante(c)
        for m in list(movs_pendientes):
            if _monto_igual(total, m.monto) and abs((c.fecha - m.fecha).days) <= 3:
                matches.append(Match(c.id, m.id, NivelMatch.MONTO_RANGO, total, m.monto))
                compras_pendientes.remove(c)
                movs_pendientes.remove(m)
                break

    # Nivel 4: Aproximado (monto +/- 2%) + fecha +/- 5 días
    for c in list(compras_pendientes):
        total = _total_comprobante(c)
        for m in list(movs_pendientes):
            if _monto_aproximado(total, m.monto) and abs((c.fecha - m.fecha).days) <= 5:
                matches.append(Match(c.id, m.id, NivelMatch.APROXIMADO, total, m.monto))
                compras_pendientes.remove(c)
                movs_pendientes.remove(m)
                break

    # Detectar diferencias: compras y movimientos sin match con fechas cercanas
    for c in compras_pendientes:
        total = _total_comprobante(c)
        for m in movs_pendientes:
            if abs((c.fecha - m.fecha).days) <= 5:
                diff = abs(total - m.monto)
                if diff > 0:
                    diferencias.append(Diferencia(
                        c.id, m.id, total, m.monto, diff,
                    ))
                break

    total_items = len(compras) + len(movimientos)
    matched_items = len(matches) * 2
    porcentaje = (matched_items / total_items * 100) if total_items > 0 else 0.0

    return ResultadoConciliacion(
        matches=matches,
        sin_match_compras=compras_pendientes,
        sin_match_banco=movs_pendientes,
        diferencias=diferencias,
        porcentaje_match=round(porcentaje, 1),
    )
