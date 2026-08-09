"""Deduplicador de movimientos bancarios."""

from app.conciliacion.movimiento import MovimientoBancario


def deduplicar(movs: list[MovimientoBancario]) -> tuple[list[MovimientoBancario], list[MovimientoBancario]]:
    """Detecta duplicados por (fecha, monto, descripcion, tipo)."""
    vistos: set[tuple] = set()
    unicos: list[MovimientoBancario] = []
    duplicados: list[MovimientoBancario] = []
    for m in movs:
        clave = (m.fecha, m.monto, m.descripcion, m.tipo)
        if clave in vistos:
            duplicados.append(m)
        else:
            vistos.add(clave)
            unicos.append(m)
    return unicos, duplicados
