"""API de Convenio Multilateral."""

from decimal import Decimal
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from app.api.clientes import RepoClientes, get_repo
from app.auth import requerir_rol
from app.convenio.atribucion import atribuir_ingresos, calcular_coeficientes

router = APIRouter(tags=["convenio"])


class ConvenioIn(BaseModel):
    ingresos: dict[str, str]


@router.post("/clientes/{cliente_id}/convenio/cm05")
def generar_cm05(
    cliente_id: int,
    datos: ConvenioIn,
    repo: RepoClientes = Depends(get_repo),
    usuario: dict = Depends(requerir_rol("owner", "senior")),
):
    cliente = repo.obtener(cliente_id)
    if cliente is None:
        raise HTTPException(status_code=404, detail="Cliente no encontrado")

    ingresos = {k: Decimal(v) for k, v in datos.ingresos.items()}
    atribucion = atribuir_ingresos(ingresos)
    coefs = calcular_coeficientes(ingresos)

    return {
        "cuit": cliente.cuit,
        "total_ingresos": str(atribucion["total_ingresos"]),
        "atribuciones": {
            k: {"ingreso": str(v["ingreso"]), "porcentaje": str(v["porcentaje"])}
            for k, v in atribucion["atribuciones"].items()
        },
        "coeficientes": {k: str(v) for k, v in coefs.items()},
    }
