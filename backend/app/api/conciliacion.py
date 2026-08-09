"""API de conciliación bancaria (Etapa 3).

POST /clientes/{id}/conciliacion/importar — sube CSV bancario y devuelve
resultado de conciliación contra las compras del cliente.
"""

from typing import Literal

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile

from app.api.clientes import RepoClientes, get_repo
from app.api.comprobantes import RepoComprobantes, get_repo_comprobantes
from app.auth import requerir_rol
from app.conciliacion.deduplicador import deduplicar
from app.conciliacion.matcher import conciliar
from app.conciliacion.parser_csv import parsear_csv

router = APIRouter(tags=["conciliacion"])


@router.post("/clientes/{cliente_id}/conciliacion/importar")
def importar_y_conciliar(
    cliente_id: int,
    archivo: UploadFile = File(...),
    delimitador: str = Form(default=";"),
    formato_numero: Literal["es_AR", "en_US"] = Form(default="es_AR"),
    repo_comp: RepoComprobantes = Depends(get_repo_comprobantes),
    repo_cli: RepoClientes = Depends(get_repo),
    usuario: dict = Depends(requerir_rol("owner", "senior")),
):
    if repo_cli.obtener(cliente_id) is None:
        raise HTTPException(status_code=404, detail="Cliente no encontrado")

    contenido = archivo.file.read()
    try:
        movs = parsear_csv(contenido, cliente_id, delimitador, formato_numero)
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))

    movs_unicos, duplicados = deduplicar(movs)
    compras = [c for c in repo_comp.de_cliente(cliente_id) if c.tipo == "compra"]
    resultado = conciliar(compras, movs_unicos)

    return {
        "porcentaje_match": resultado.porcentaje_match,
        "matches": [
            {
                "comprobante_id": m.comprobante_id,
                "movimiento_id": m.movimiento_id,
                "nivel": m.nivel.value,
                "monto_comprobante": str(m.monto_comprobante),
                "monto_movimiento": str(m.monto_movimiento),
            }
            for m in resultado.matches
        ],
        "sin_match_compras": [c.id for c in resultado.sin_match_compras],
        "sin_match_banco": [
            {"id": m.id, "fecha": m.fecha.isoformat(), "descripcion": m.descripcion, "monto": str(m.monto)}
            for m in resultado.sin_match_banco
        ],
        "diferencias": [
            {
                "comprobante_id": d.comprobante_id,
                "movimiento_id": d.movimiento_id,
                "monto_diferencia": str(d.monto_diferencia),
            }
            for d in resultado.diferencias
        ],
        "duplicados": len(duplicados),
        "importados": len(movs),
        "periodo": compras[0].periodo if compras else "",
        "confirmado_por": usuario["sub"],
    }
