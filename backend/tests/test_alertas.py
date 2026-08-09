from decimal import Decimal
from datetime import date

from app.iva.alertas import analizar_alertas, AlertaIva
from app.iva.calculadora import liquidacion_iva
from app.iva.comprobante import ComprobanteIva, AlicuotaLinea


def _comp(tipo, fecha, alicuota, neto, iva):
    return ComprobanteIva(
        id=1, cliente_id=1, tipo=tipo, fecha=date.fromisoformat(fecha),
        lineas=[AlicuotaLinea(Decimal(alicuota), Decimal(neto), Decimal(iva))],
        confirmado_por="test", confirmado_en=None,
    )


def test_sin_alertas_cuando_debito_mayor():
    ventas = [_comp("venta", "2026-08-01", "0.21", "100000", "21000")]
    compras = [_comp("compra", "2026-08-01", "0.21", "50000", "10500")]
    liq = liquidacion_iva(ventas, compras, Decimal("0"))
    alertas = analizar_alertas(liq, historial_saldos_favor=[])
    assert len(alertas) == 0


def test_salto_credito_fiscal_warning():
    # debito 21000, credito 40000 (>50% del débito)
    ventas = [_comp("venta", "2026-08-01", "0.21", "100000", "21000")]
    compras = [_comp("compra", "2026-08-01", "0.21", "190476", "40000")]
    liq = liquidacion_iva(ventas, compras, Decimal("0"))
    alertas = analizar_alertas(liq, historial_saldos_favor=[])
    assert any(a.codigo == "salto_credito_fiscal" and a.nivel == "warning" for a in alertas)


def test_salto_credito_fiscal_critical():
    # debito 21000, credito 50000 (>100% del débito)
    ventas = [_comp("venta", "2026-08-01", "0.21", "100000", "21000")]
    compras = [_comp("compra", "2026-08-01", "0.21", "238095", "50000")]
    liq = liquidacion_iva(ventas, compras, Decimal("0"))
    alertas = analizar_alertas(liq, historial_saldos_favor=[])
    assert any(a.codigo == "salto_credito_fiscal" and a.nivel == "critical" for a in alertas)


def test_iva_tecnico_acumulado_warning():
    ventas = [_comp("venta", "2026-08-01", "0.21", "100000", "21000")]
    compras = [_comp("compra", "2026-08-01", "0.21", "200000", "42000")]
    liq = liquidacion_iva(ventas, compras, Decimal("0"))
    historial = [Decimal("5000"), Decimal("8000")]  # 2 períodos previos con saldo a favor
    alertas = analizar_alertas(liq, historial_saldos_favor=historial)
    assert any(a.codigo == "iva_tecnico_acumulado" and a.nivel == "warning" for a in alertas)


def test_info_saldo_favor_parcial():
    ventas = [_comp("venta", "2026-08-01", "0.21", "100000", "21000")]
    compras = [_comp("compra", "2026-08-01", "0.21", "50000", "10500")]
    liq = liquidacion_iva(ventas, compras, Decimal("5000"))
    alertas = analizar_alertas(liq, historial_saldos_favor=[])
    assert any(a.codigo == "saldo_favor_parcial" and a.nivel == "info" for a in alertas)
