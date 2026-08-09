from decimal import Decimal
from unittest.mock import MagicMock

from app.facturacion.factura import SolicitudFactura, TipoComprobante
from app.facturacion.emisor import emitir_factura


def test_emitir_factura_b_exitosa():
    mock_wsfe = MagicMock()
    mock_wsfe.fecae_solicitar.return_value = {
        "CAE": "12345678901234",
        "CAEFchVto": "20260818",
        "CbteDesde": 1,
        "Resultado": "A",
    }

    sol = SolicitudFactura(
        tipo=TipoComprobante.FACTURA_B,
        punto_venta=1,
        numero=0,
        fecha="2026-08-08",
        receptor_cuit="20345678901",
        receptor_razon="Cliente Prueba",
        receptor_condicion="RI",
        neto=Decimal("10000"),
        iva=Decimal("2100"),
        total=Decimal("12100"),
    )

    res = emitir_factura(sol, cuit_emisor="20273965239", wsfe=mock_wsfe)
    assert res.cae == "12345678901234"
    assert res.estado == "A"
    assert res.numero == 1


def test_emitir_factura_rechazada():
    mock_wsfe = MagicMock()
    mock_wsfe.fecae_solicitar.return_value = {
        "CAE": "",
        "Resultado": "R",
        "Observaciones": [{"Code": 100, "Msg": "Error"}],
    }

    sol = SolicitudFactura(
        tipo=TipoComprobante.FACTURA_B,
        punto_venta=1, numero=0, fecha="2026-08-08",
        receptor_cuit="20345678901", receptor_razon="X", receptor_condicion="RI",
        neto=Decimal("10000"), iva=Decimal("2100"), total=Decimal("12100"),
    )

    res = emitir_factura(sol, cuit_emisor="20273965239", wsfe=mock_wsfe)
    assert res.estado == "R"
    assert res.cae == ""
    assert len(res.observaciones) == 1
