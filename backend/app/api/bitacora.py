"""API de bitácora de revisión."""

from fastapi import APIRouter, Depends
from pydantic import BaseModel

from app.auth import requerir_rol
from app.bitacora.modelo import registrar_revision, listar_revisiones

router = APIRouter(tags=["bitacora"])


class RevisionIn(BaseModel):
    entidad_tipo: str
    entidad_id: int
    estado: str
    comentario: str = ""


@router.post("/revisiones", status_code=201)
def crear_revision(
    datos: RevisionIn,
    usuario: dict = Depends(requerir_rol("owner", "senior")),
):
    rev = registrar_revision(
        entidad_tipo=datos.entidad_tipo,
        entidad_id=datos.entidad_id,
        usuario=usuario["sub"],
        estado=datos.estado,
        comentario=datos.comentario,
    )
    return {
        "id": rev.id,
        "entidad_tipo": rev.entidad_tipo,
        "entidad_id": rev.entidad_id,
        "usuario": rev.usuario,
        "estado": rev.estado,
        "comentario": rev.comentario,
        "timestamp": rev.timestamp.isoformat(),
    }


@router.get("/revisiones/{entidad_tipo}/{entidad_id}")
def get_revisiones(
    entidad_tipo: str,
    entidad_id: int,
    usuario: dict = Depends(requerir_rol("owner", "senior")),
):
    revs = listar_revisiones(entidad_tipo, entidad_id)
    return [
        {
            "id": r.id,
            "usuario": r.usuario,
            "estado": r.estado,
            "comentario": r.comentario,
            "timestamp": r.timestamp.isoformat(),
        }
        for r in revs
    ]
