"""API de facturación con CAE (Etapa 4).

POST /clientes/{id}/facturacion/emitir — emite factura electrónica,
genera PDF, y registra automáticamente la venta.
"""

from decimal import Decimal
from typing import Literal

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from app.api.clientes import RepoClientes, get_repo
from app.api.comprobantes import RepoComprobantes, get_repo_comprobantes
from app.auth import requerir_rol
from app.facturacion.emisor import emitir_factura
from app.facturacion.factura import SolicitudFactura, TipoComprobante, calcular_iva
from app.facturacion.pdf_generator import generar_pdf

router = APIRouter(tags=["facturacion"])


class FacturaIn(BaseModel):
    tipo: Literal["FACTURA_A", "FACTURA_B", "FACTURA_C", "FACTURA_M",
                  "NOTA_CREDITO_A", "NOTA_CREDITO_B", "NOTA_CREDITO_C",
                  "NOTA_DEBITO_A", "NOTA_DEBITO_B", "NOTA_DEBITO_C"]
    punto_venta: int
    numero: int = 0
    fecha: str
    receptor_cuit: str
    receptor_razon: str
    receptor_condicion: Literal["RI", "MT", "EX", "CF"]
    neto: Decimal
    alicuota: Decimal = Decimal("0.21")
    total: Decimal | None = None


def _crear_wsfe_client(cuit_emisor: str):
    """Factory para crear cliente WSFE."""
    from app.arca.wsaa import get_ticket
    from app.arca.wsfe import WsfeClient
    from app.arca.config import ARCA_HOMOLOGACION
    ta = get_ticket(cuit=cuit_emisor, service="wsfe")
    return WsfeClient(ta=ta, cuit=cuit_emisor, homologacion=ARCA_HOMOLOGACION)


@router.post("/clientes/{cliente_id}/facturacion/emitir", status_code=201)
def emitir(
    cliente_id: int,
    datos: FacturaIn,
    repo_cli: RepoClientes = Depends(get_repo),
    repo_comp: RepoComprobantes = Depends(get_repo_comprobantes),
    usuario: dict = Depends(requerir_rol("owner", "senior")),
):
    cliente = repo_cli.obtener(cliente_id)
    if cliente is None:
        raise HTTPException(status_code=404, detail="Cliente no encontrado")

    iva = calcular_iva(datos.neto, datos.alicuota)
    total = datos.total if datos.total is not None else datos.neto + iva

    tipo_enum = TipoComprobante[datos.tipo]
    solicitud = SolicitudFactura(
        tipo=tipo_enum,
        punto_venta=datos.punto_venta,
        numero=datos.numero,
        fecha=datos.fecha,
        receptor_cuit=datos.receptor_cuit,
        receptor_razon=datos.receptor_razon,
        receptor_condicion=datos.receptor_condicion,
        neto=datos.neto,
        iva=iva,
        total=total,
    )

    try:
        wsfe = _crear_wsfe_client(cliente.cuit)
        resultado = emitir_factura(solicitud, cuit_emisor=cliente.cuit, wsfe=wsfe)
    except Exception as e:
        raise HTTPException(status_code=503, detail=f"WSFE no disponible: {e}")

    if resultado.estado == "R":
        raise HTTPException(status_code=422, detail={
            "error": "Factura rechazada por ARCA",
            "observaciones": resultado.observaciones,
        })

    from app.api.comprobantes import ComprobanteIn

    repo_comp.crear(cliente_id, ComprobanteIn(
        tipo="venta",
        fecha=datos.fecha,
        lineas=[{"alicuota": datos.alicuota, "neto": datos.neto, "iva": iva}],
    ), confirmado_por=f"wsfe:{usuario['sub']}")

    pdf_bytes = generar_pdf(solicitud, resultado, cliente.cuit)

    return {
        "cae": resultado.cae,
        "vencimiento_cae": resultado.vencimiento_cae,
        "numero": resultado.numero,
        "tipo": datos.tipo,
        "punto_venta": datos.punto_venta,
        "total": str(total),
        "pdf_base64": pdf_bytes.hex(),
    }
