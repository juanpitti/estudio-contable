"""Normalizador: payload crudo del QR AFIP → campos del comprobante.

Cada campo declara su fuente y confianza. El CUIT se revalida con el
dígito verificador: si no cierra, la confianza cae y el comprobante
entero queda marcado para revisión (trazabilidad, Plan v4 regla 6).
"""

from app.cuit import formatear_cuit
from app.extractor.tipos import CampoExtraido


def normalizar_qr(payload: dict) -> dict[str, CampoExtraido]:
    campos: dict[str, CampoExtraido] = {}

    cuit_crudo = str(payload.get("cuit", ""))
    try:
        cuit = formatear_cuit(cuit_crudo)
        campos["cuit"] = CampoExtraido(cuit, 1.0, "qr")
    except ValueError:
        # El QR se leyó pero el CUIT no valida: baja confianza, revisar
        campos["cuit"] = CampoExtraido(cuit_crudo, 0.3, "qr")

    campos["pto_vta"] = CampoExtraido(int(payload.get("ptoVta", 0)), 1.0, "qr")
    campos["tipo"] = CampoExtraido(int(payload.get("tipoCmp", 0)), 1.0, "qr")
    campos["nro"] = CampoExtraido(int(payload.get("nroCmp", 0)), 1.0, "qr")
    campos["fecha"] = CampoExtraido(str(payload.get("fecha", "")), 1.0, "qr")
    campos["importe"] = CampoExtraido(float(payload.get("importe", 0.0)), 1.0, "qr")
    campos["cae"] = CampoExtraido(str(payload.get("codAut", "")), 1.0, "qr")
    return campos
