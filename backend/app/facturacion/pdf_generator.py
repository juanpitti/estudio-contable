"""Generador de PDF de factura con QR AFIP."""

import os
import tempfile
from io import BytesIO

from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.pdfgen import canvas
import qrcode

from app.facturacion.factura import SolicitudFactura
from app.facturacion.emisor import ResultadoEmision


def _generar_qr(cuit_emisor: str, tipo_cbte: int, pto_vta: int, cae: str, vto_cae: str, total: str) -> bytes:
    """Genera QR AFIP según especificación simplificada."""
    qr_data = f"https://www.afip.gob.ar/fe/qr/?p={{" \
               f"'ver':1,'fecha':'2026-08-08','cuit':{cuit_emisor}," \
               f"'ptoVta':{pto_vta},'tipoCmp':{tipo_cbte},'nroCmp':1," \
               f"'importe':{total},'moneda':'PES','ctz':1," \
               f"'tipoDocRec':80,'nroDocRec':20345678901," \
               f"'tipoCodAut':'E','codAut':{cae}}}"
    qr = qrcode.make(qr_data[:500])  # truncar para demo
    buf = BytesIO()
    qr.save(buf, format="PNG")
    buf.seek(0)
    return buf.read()


def generar_pdf(solicitud: SolicitudFactura, resultado: ResultadoEmision, cuit_emisor: str) -> bytes:
    buf = BytesIO()
    c = canvas.Canvas(buf, pagesize=A4)
    width, height = A4

    # Header
    c.setFont("Helvetica-Bold", 16)
    c.drawString(20 * mm, height - 20 * mm, f"FACTURA {solicitud.tipo.name.replace('_', ' ')}")
    c.setFont("Helvetica", 10)
    c.drawString(20 * mm, height - 28 * mm, f"Punto de Venta: {solicitud.punto_venta:04d} - Número: {resultado.numero:08d}")
    c.drawString(20 * mm, height - 33 * mm, f"Fecha: {solicitud.fecha}")

    # Emisor
    c.setFont("Helvetica-Bold", 10)
    c.drawString(20 * mm, height - 45 * mm, "EMISOR")
    c.setFont("Helvetica", 10)
    c.drawString(20 * mm, height - 50 * mm, f"CUIT: {cuit_emisor}")

    # Receptor
    c.setFont("Helvetica-Bold", 10)
    c.drawString(20 * mm, height - 60 * mm, "RECEPTOR")
    c.setFont("Helvetica", 10)
    c.drawString(20 * mm, height - 65 * mm, f"Razón Social: {solicitud.receptor_razon}")
    c.drawString(20 * mm, height - 70 * mm, f"CUIT: {solicitud.receptor_cuit}")
    c.drawString(20 * mm, height - 75 * mm, f"Condición IVA: {solicitud.receptor_condicion}")

    # Items
    c.setFont("Helvetica-Bold", 10)
    c.drawString(20 * mm, height - 90 * mm, "CONCEPTO")
    c.drawString(120 * mm, height - 90 * mm, "IMPORTE")
    c.line(20 * mm, height - 92 * mm, 180 * mm, height - 92 * mm)
    
    c.setFont("Helvetica", 10)
    c.drawString(20 * mm, height - 98 * mm, "Servicios / Productos")
    c.drawString(120 * mm, height - 98 * mm, f"${float(solicitud.neto):,.2f}")

    # Totales
    c.line(20 * mm, height - 110 * mm, 180 * mm, height - 110 * mm)
    c.setFont("Helvetica", 10)
    c.drawString(120 * mm, height - 116 * mm, f"Neto: ${float(solicitud.neto):,.2f}")
    c.drawString(120 * mm, height - 121 * mm, f"IVA 21%: ${float(solicitud.iva):,.2f}")
    c.setFont("Helvetica-Bold", 12)
    c.drawString(120 * mm, height - 128 * mm, f"TOTAL: ${float(solicitud.total):,.2f}")

    # CAE
    c.setFont("Helvetica-Bold", 10)
    c.drawString(20 * mm, height - 140 * mm, "CAE")
    c.setFont("Helvetica", 10)
    c.drawString(20 * mm, height - 145 * mm, resultado.cae)
    c.drawString(20 * mm, height - 150 * mm, f"Vencimiento CAE: {resultado.vencimiento_cae}")

    # QR - guardar en archivo temporal para drawImage
    qr_bytes = _generar_qr(
        cuit_emisor, solicitud.tipo.value, solicitud.punto_venta,
        resultado.cae, resultado.vencimiento_cae, str(solicitud.total),
    )
    with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as tmp:
        tmp.write(qr_bytes)
        tmp_path = tmp.name
    c.drawImage(tmp_path, 140 * mm, height - 170 * mm, width=40 * mm, height=40 * mm)
    os.unlink(tmp_path)

    c.save()
    buf.seek(0)
    return buf.read()
