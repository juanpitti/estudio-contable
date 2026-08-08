"""Tests de la liquidación de IVA — importes calculados a mano.

Caso base: venta neta 100.000 @21% → débito 21.000
           compra neta 50.000 @21% → crédito 10.500
"""

from datetime import date
from decimal import Decimal

from app.iva.calculadora import liquidacion_iva
from app.iva.comprobante import AlicuotaLinea, ComprobanteIva

A21 = Decimal("0.21")
A105 = Decimal("0.105")
A27 = Decimal("0.27")


def _comp(tipo, lineas, fecha=date(2026, 8, 15)):
    return ComprobanteIva(
        id=1,
        cliente_id=1,
        tipo=tipo,
        fecha=fecha,
        lineas=lineas,
        confirmado_por="owner",
        confirmado_en=None,
    )


def test_debito_menos_credito_da_saldo_a_pagar():
    ventas = [_comp("venta", [AlicuotaLinea(A21, Decimal("100000"), Decimal("21000"))])]
    compras = [_comp("compra", [AlicuotaLinea(A21, Decimal("50000"), Decimal("10500"))])]
    liq = liquidacion_iva(ventas, compras, Decimal("0"))
    assert liq.debito[A21] == Decimal("21000")
    assert liq.credito[A21] == Decimal("10500")
    assert liq.saldo_a_pagar == Decimal("10500")
    assert liq.saldo_a_favor_final == Decimal("0")


def test_credito_mayor_que_debito_es_saldo_a_favor_iva_tecnico():
    ventas = [_comp("venta", [AlicuotaLinea(A21, Decimal("100000"), Decimal("21000"))])]
    compras = [_comp("compra", [AlicuotaLinea(A21, Decimal("142857.15"), Decimal("30000"))])]
    liq = liquidacion_iva(ventas, compras, Decimal("0"))
    assert liq.saldo_a_pagar == Decimal("0")
    assert liq.saldo_a_favor_final == Decimal("9000")


def test_saldo_favor_anterior_se_descuenta():
    ventas = [_comp("venta", [AlicuotaLinea(A21, Decimal("100000"), Decimal("21000"))])]
    compras = [_comp("compra", [AlicuotaLinea(A21, Decimal("50000"), Decimal("10500"))])]
    liq = liquidacion_iva(ventas, compras, Decimal("5000"))
    assert liq.saldo_a_pagar == Decimal("5500")
    assert liq.saldo_a_favor_final == Decimal("0")


def test_saldo_favor_anterior_supera_al_resultado():
    ventas = [_comp("venta", [AlicuotaLinea(A21, Decimal("100000"), Decimal("21000"))])]
    compras = [_comp("compra", [AlicuotaLinea(A21, Decimal("50000"), Decimal("10500"))])]
    liq = liquidacion_iva(ventas, compras, Decimal("20000"))
    assert liq.saldo_a_pagar == Decimal("0")
    assert liq.saldo_a_favor_final == Decimal("9500")  # 20000 - 10500


def test_desglose_por_alicuotas_multiples():
    ventas = [
        _comp("venta", [AlicuotaLinea(A21, Decimal("100000"), Decimal("21000"))]),
        _comp(
            "venta",
            [
                AlicuotaLinea(A105, Decimal("20000"), Decimal("2100")),
                AlicuotaLinea(A27, Decimal("10000"), Decimal("2700")),
            ],
        ),
    ]
    liq = liquidacion_iva(ventas, [], Decimal("0"))
    assert liq.debito[A21] == Decimal("21000")
    assert liq.debito[A105] == Decimal("2100")
    assert liq.debito[A27] == Decimal("2700")
    assert liq.saldo_a_pagar == Decimal("25800")


def test_sin_comprobantes_todo_en_cero():
    liq = liquidacion_iva([], [], Decimal("0"))
    assert liq.saldo_a_pagar == Decimal("0")
    assert liq.saldo_a_favor_final == Decimal("0")
    assert liq.debito == {}
