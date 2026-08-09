"""API de monotributo."""

from decimal import Decimal
from fastapi import APIRouter, Depends, HTTPException

from app.api.clientes import RepoClientes, get_repo
from app.auth import requerir_rol
from app.monotributo.categoria import categoria_para_ingresos, proyeccion_categoria, alerta_proximidad_techo

router = APIRouter(tags=["monotributo"])


@router.get("/clientes/{cliente_id}/monotributo")
def get_monotributo(
    cliente_id: int,
    repo: RepoClientes = Depends(get_repo),
    usuario: dict = Depends(requerir_rol("owner", "senior")),
):
    cliente = repo.obtener(cliente_id)
    if cliente is None:
        raise HTTPException(status_code=404, detail="Cliente no encontrado")

    ingresos_mensuales = [Decimal("800000")] * 6
    categoria_actual = "A"

    proj = proyeccion_categoria(ingresos_mensuales, categoria_actual)
    cat = categoria_para_ingresos(Decimal(proj["ingresos_acumulados"]))
    alerta = alerta_proximidad_techo(Decimal(proj["ingresos_acumulados"]), categoria_actual)

    return {
        "categoria_actual": proj["categoria_actual"],
        "categoria_proyectada": proj["categoria_proyectada"],
        "ingresos_acumulados": proj["ingresos_acumulados"],
        "techo_actual": proj["techo_actual"],
        "porcentaje_del_techo": proj["porcentaje_del_techo"],
        "alerta": alerta,
        "cuota_mensual": str(cat.total_mensual) if cat else None,
    }
