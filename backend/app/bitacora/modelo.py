"""Bitácora de revisión humana — Ley 20.488."""

from dataclasses import dataclass
from datetime import datetime


@dataclass
class Revision:
    id: int
    entidad_tipo: str
    entidad_id: int
    usuario: str
    estado: str  # "revisado", "aprobado", "rechazado"
    comentario: str
    timestamp: datetime


_REVISIONES: list[Revision] = []
_ULTIMO_ID = 0


def registrar_revision(
    entidad_tipo: str,
    entidad_id: int,
    usuario: str,
    estado: str,
    comentario: str = "",
) -> Revision:
    global _ULTIMO_ID
    _ULTIMO_ID += 1
    rev = Revision(
        id=_ULTIMO_ID,
        entidad_tipo=entidad_tipo,
        entidad_id=entidad_id,
        usuario=usuario,
        estado=estado,
        comentario=comentario,
        timestamp=datetime.now(),
    )
    _REVISIONES.append(rev)
    return rev


def listar_revisiones(entidad_tipo: str, entidad_id: int) -> list[Revision]:
    return [r for r in _REVISIONES if r.entidad_tipo == entidad_tipo and r.entidad_id == entidad_id]


def _limpiar_revisiones() -> None:
    _REVISIONES.clear()
    global _ULTIMO_ID
    _ULTIMO_ID = 0


def obtener_ultima_revision(entidad_tipo: str, entidad_id: int) -> Revision | None:
    revs = listar_revisiones(entidad_tipo, entidad_id)
    return revs[-1] if revs else None
    _REVISIONES.clear()
    global _ULTIMO_ID
    _ULTIMO_ID = 0
    revs = listar_revisiones(entidad_tipo, entidad_id)
    return revs[-1] if revs else None
