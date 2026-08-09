from decimal import Decimal
from datetime import date

from app.conciliacion.movimiento import MovimientoBancario
from app.conciliacion.matcher import conciliar, NivelMatch
from app.iva.comprobante import ComprobanteIva, AlicuotaLinea


def _comp(id, fecha, neto, iva):
    return ComprobanteIva(
        id=id, cliente_id=1, tipo="compra", fecha=date.fromisoformat(fecha),
        lineas=[AlicuotaLinea(Decimal("0.21"), Decimal(neto), Decimal(iva))],
        confirmado_por="test", confirmado_en=None,
    )


def _mov(id, fecha, monto, desc="PAGO"):
    return MovimientoBancario(
        id=id, cliente_id=1, fecha=date.fromisoformat(fecha),
        descripcion=desc, monto=Decimal(str(monto)), tipo="debito",
    )


def test_match_exacto():
    comps = [_comp(1, "2026-08-01", "10000", "2100")]  # total 12100
    movs = [_mov(1, "2026-08-01", 12100)]
    res = conciliar(comps, movs)
    assert len(res.matches) == 1
    assert res.matches[0].nivel == NivelMatch.EXACTO
    assert res.porcentaje_match == 100.0


def test_match_monto_fecha():
    comps = [_comp(1, "2026-08-01", "10000", "2100")]
    movs = [_mov(1, "2026-08-01", 12100, "TRANSFERENCIA")]
    res = conciliar(comps, movs)
    assert len(res.matches) == 1
    assert res.matches[0].nivel == NivelMatch.EXACTO  # mismo que exacto en esta iteración


def test_match_monto_rango():
    comps = [_comp(1, "2026-08-01", "10000", "2100")]
    movs = [_mov(1, "2026-08-04", 12100)]  # +3 días
    res = conciliar(comps, movs)
    assert len(res.matches) == 1
    assert res.matches[0].nivel == NivelMatch.MONTO_RANGO


def test_match_aproximado():
    comps = [_comp(1, "2026-08-01", "10000", "2100")]  # 12100
    movs = [_mov(1, "2026-08-06", 12000)]  # -100 (0.8% diff), +5 días
    res = conciliar(comps, movs)
    assert len(res.matches) == 1
    assert res.matches[0].nivel == NivelMatch.APROXIMADO


def test_sin_match():
    comps = [_comp(1, "2026-08-01", "10000", "2100")]
    movs = [_mov(1, "2026-08-15", 5000)]
    res = conciliar(comps, movs)
    assert len(res.matches) == 0
    assert len(res.sin_match_compras) == 1
    assert len(res.sin_match_banco) == 1


def test_diferencia_detectada():
    comps = [_comp(1, "2026-08-01", "10000", "2100")]  # 12100
    movs = [_mov(1, "2026-08-01", 15000)]  # 2900 de diferencia
    res = conciliar(comps, movs)
    assert len(res.matches) == 0
    assert len(res.sin_match_compras) == 1
    assert len(res.sin_match_banco) == 1
    assert len(res.diferencias) == 1
    assert res.diferencias[0].monto_diferencia == Decimal("2900")
