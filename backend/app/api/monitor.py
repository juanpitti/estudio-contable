"""API de monitor fiscal."""

from fastapi import APIRouter, Depends

from app.api.clientes import RepoClientes, get_repo
from app.auth import requerir_rol
from app.monitor.fiscal import monitor_global, resumen_estudio

router = APIRouter(tags=["monitor"])


@router.get("/monitor")
def get_monitor(
    repo: RepoClientes = Depends(get_repo),
    usuario: dict = Depends(requerir_rol("owner", "senior")),
):
    clientes = repo.listar()
    clientes_dict = [
        {"id": c.id, "ingresos_acumulados": "800000", "categoria_monotributo": "A"}
        for c in clientes
    ]

    alertas = monitor_global(clientes_dict)
    resumen = resumen_estudio(clientes_dict)

    return {
        "alertas": [
            {
                "nivel": a.nivel,
                "codigo": a.codigo,
                "mensaje": a.mensaje,
                "cliente_id": a.cliente_id,
                "accion_sugerida": a.accion_sugerida,
            }
            for a in alertas
        ],
        "resumen": resumen,
    }
