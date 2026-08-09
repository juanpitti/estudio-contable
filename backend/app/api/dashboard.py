"""API de dashboard / tablero de cartera."""

from fastapi import APIRouter, Depends

from app.api.clientes import RepoClientes, get_repo
from app.auth import requerir_rol
from app.calendario.vencimientos import alertas_vencimientos_proximos, proximos_vencimientos
from app.bitacora.modelo import obtener_ultima_revision

router = APIRouter(tags=["dashboard"])


@router.get("/dashboard")
def get_dashboard(
    repo: RepoClientes = Depends(get_repo),
    usuario: dict = Depends(requerir_rol("owner", "senior")),
):
    clientes = repo.listar()
    semaforos = []
    for c in clientes:
        ultima = obtener_ultima_revision("liquidacion_iva", c.id)
        estado = "verde" if ultima and ultima.estado == "aprobado" else "amarillo"
        semaforos.append({
            "id": c.id,
            "razon_social": c.razon_social,
            "cuit": c.cuit,
            "condicion_iva": c.condicion_iva,
            "semaforo": estado,
            "ultima_revision": ultima.timestamp.isoformat() if ultima else None,
        })

    vencs = proximos_vencimientos(dias=30)
    alertas = alertas_vencimientos_proximos(dias_ventana=7)

    return {
        "clientes": semaforos,
        "vencimientos_proximos": [
            {"impuesto": v.impuesto, "fecha": v.fecha.isoformat(), "periodicidad": v.periodicidad}
            for v in vencs
        ],
        "alertas": alertas,
    }
