from decimal import Decimal

from app.facturacion.factura import SolicitudFactura, TipoComprobante, calcular_iva


def test_solicitud_factura_valida():
    sol = SolicitudFactura(
        tipo=TipoComprobante.FACTURA_B,
        punto_venta=1,
        numero=1,
        fecha="2026-08-08",
        receptor_cuit="20345678901",
        receptor_razon="Cliente Prueba",
        receptor_condicion="RI",
        neto=Decimal("10000"),
        iva=Decimal("2100"),
        total=Decimal("12100"),
    )
    assert sol.tipo == TipoComprobante.FACTURA_B
    assert sol.total == Decimal("12100")


def test_calcular_iva_21():
    assert calcular_iva(Decimal("10000"), Decimal("0.21")) == Decimal("2100")


def test_calcular_iva_10_5():
    assert calcular_iva(Decimal("10000"), Decimal("0.105")) == Decimal("1050")
