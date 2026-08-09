"""Servicio de emisión de facturas vía WSFE."""

from dataclasses import dataclass
from decimal import Decimal

from app.facturacion.factura import SolicitudFactura, TipoComprobante


@dataclass(frozen=True)
class ResultadoEmision:
    cae: str
    vencimiento_cae: str
    numero: int
    estado: str  # A=aprobado, R=rechazado
    observaciones: list[dict]


def _tipo_cbte(tipo: TipoComprobante) -> int:
    return tipo.value


def _condicion_iva_receptor(cod: str) -> int:
    """Mapea condición fiscal a código IVA de receptor."""
    mapping = {
        "RI": 1,   # IVA Responsable Inscripto
        "MT": 6,   # Monotributo
        "EX": 4,   # Sujeto exento
        "CF": 5,   # Consumidor final
    }
    return mapping.get(cod, 5)


def _alicuota_wsfe(alic: Decimal) -> int:
    """Mapea alícuota a código WSFE."""
    if alic == Decimal("0.21"):
        return 5
    if alic == Decimal("0.105"):
        return 4
    if alic == Decimal("0.27"):
        return 6
    return 5


def emitir_factura(
    solicitud: SolicitudFactura,
    cuit_emisor: str,
    wsfe,
) -> ResultadoEmision:
    """Emite factura vía WSFE y devuelve resultado."""
    tipo_cbte = _tipo_cbte(solicitud.tipo)
    pto_vta = solicitud.punto_venta
    
    # Construir solicitud WSFE
    comp = {
        "Concepto": solicitud.concepto,
        "DocTipo": 80 if len(solicitud.receptor_cuit) == 11 else 96,  # 80=CUIT, 96=DNI
        "DocNro": int(solicitud.receptor_cuit.replace("-", "")),
        "CbteDesde": solicitud.numero or 1,
        "CbteHasta": solicitud.numero or 1,
        "CbteFch": solicitud.fecha.replace("-", ""),
        "ImpTotal": float(solicitud.total),
        "ImpTotConc": 0,
        "ImpNeto": float(solicitud.neto),
        "ImpOpEx": 0,
        "ImpIVA": float(solicitud.iva),
        "ImpTrib": 0,
        "MonId": "PES",
        "MonCotiz": 1,
        "Iva": [
            {
                "Id": _alicuota_wsfe(Decimal("0.21")),
                "BaseImp": float(solicitud.neto),
                "Importe": float(solicitud.iva),
            }
        ],
    }

    # Agregar condición IVA receptor si es factura A/M
    if tipo_cbte in (1, 51):  # Factura A o M
        comp["IvaId"] = _condicion_iva_receptor(solicitud.receptor_condicion)

    resultado = wsfe.fecae_solicitar(pto_vta=pto_vta, tipo_cbte=tipo_cbte, comprobantes=[comp])

    # Extraer resultado
    obs = resultado.get("Observaciones", [])
    if isinstance(obs, list):
        observaciones = [{"code": o.get("Code", ""), "msg": o.get("Msg", "")} for o in obs]
    else:
        observaciones = []

    return ResultadoEmision(
        cae=str(resultado.get("CAE", "")),
        vencimiento_cae=str(resultado.get("CAEFchVto", "")),
        numero=int(resultado.get("CbteDesde", 0)),
        estado=str(resultado.get("Resultado", "R")),
        observaciones=observaciones,
    )
