"""API del asistente IA."""

from fastapi import APIRouter, Depends
from pydantic import BaseModel

from app.api.clientes import RepoClientes, get_repo
from app.auth import requerir_rol
from app.asistente.motor import responder
from app.calendario.vencimientos import proximos_vencimientos
from app.monitor.fiscal import monitor_global

router = APIRouter(tags=["asistente"])


class PreguntaIn(BaseModel):
    pregunta: str


@router.post("/asistente")
def consultar_asistente(
    datos: PreguntaIn,
    repo: RepoClientes = Depends(get_repo),
    usuario: dict = Depends(requerir_rol("owner", "senior")),
):
    clientes = repo.listar()
    clientes_dict = [
        {"id": c.id, "razon_social": c.razon_social, "semaforo": "amarillo"}
        for c in clientes
    ]

    vencs = proximos_vencimientos(dias=7)
    vencs_dict = [
        {"impuesto": v.impuesto, "fecha": v.fecha.isoformat(), "dias_restantes": (v.fecha.day)}
        for v in vencs
    ]

    alertas = [
        {"nivel": a.nivel, "codigo": a.codigo, "cliente_id": a.cliente_id}
        for a in monitor_global(clientes_dict)
    ]

    respuesta = responder(datos.pregunta, clientes_dict, alertas, vencs_dict)

    return {
        "texto": respuesta.texto,
        "fuente": respuesta.fuente,
        "links": list(respuesta.links) if respuesta.links else [],
    }
