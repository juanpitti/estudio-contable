from decimal import Decimal

from app.facturacion.factura import SolicitudFactura, TipoComprobante
from app.facturacion.emisor import ResultadoEmision
from app.facturacion.pdf_generator import generar_pdf


def test_genera_pdf_no_vacio():
    sol = SolicitudFactura(
        tipo=TipoComprobante.FACTURA_B,
        punto_venta=1, numero=1, fecha="2026-08-08",
        receptor_cuit="20345678901", receptor_razon="Cliente Prueba", receptor_condicion="RI",
        neto=Decimal("10000"), iva=Decimal("2100"), total=Decimal("12100"),
    )
    res = ResultadoEmision(
        cae="12345678901234", vencimiento_cae="20260818",
        numero=1, estado="A", observaciones=[],
    )
    data = generar_pdf(sol, res, cuit_emisor="20273965239")
    assert len(data) > 0
    assert data[:4] == b"%PDF"
