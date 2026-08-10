"""Bitácora de revisión humana — Ley 20.488.

Repositorio SQLAlchemy inyectable.
"""

from datetime import datetime, timezone
from dataclasses import dataclass

from sqlalchemy.orm import Session

from app.database import get_db
from app.models_db import DBRevision


@dataclass
class Revision:
    id: int
    entidad_tipo: str
    entidad_id: int
    usuario: str
    estado: str  # "revisado", "aprobado", "rechazado"
    comentario: str
    timestamp: datetime


class RepoRevisiones:
    def __init__(self, db: Session) -> None:
        self._db = db

    def registrar(
        self,
        entidad_tipo: str,
        entidad_id: int,
        usuario: str,
        estado: str,
        comentario: str = "",
    ) -> Revision:
        db_rev = DBRevision(
            entidad_tipo=entidad_tipo,
            entidad_id=entidad_id,
            usuario=usuario,
            estado=estado,
            comentario=comentario,
            timestamp=datetime.now(timezone.utc),
        )
        self._db.add(db_rev)
        self._db.commit()
        self._db.refresh(db_rev)
        return self._to_domain(db_rev)

    def listar(self, entidad_tipo: str, entidad_id: int) -> list[Revision]:
        revs = self._db.query(DBRevision).filter_by(
            entidad_tipo=entidad_tipo, entidad_id=entidad_id
        ).all()
        return [self._to_domain(r) for r in revs]

    def obtener_ultima(self, entidad_tipo: str, entidad_id: int) -> Revision | None:
        rev = self._db.query(DBRevision).filter_by(
            entidad_tipo=entidad_tipo, entidad_id=entidad_id
        ).order_by(DBRevision.timestamp.desc()).first()
        return self._to_domain(rev) if rev else None

    @staticmethod
    def _to_domain(db_rev: DBRevision) -> Revision:
        return Revision(
            id=db_rev.id,
            entidad_tipo=db_rev.entidad_tipo,
            entidad_id=db_rev.entidad_id,
            usuario=db_rev.usuario,
            estado=db_rev.estado,
            comentario=db_rev.comentario,
            timestamp=db_rev.timestamp,
        )


# Funciones de compatibilidad para módulos que no usan inyección de dependencias
_repo_global: RepoRevisiones | None = None


def _get_global_repo() -> RepoRevisiones:
    global _repo_global
    if _repo_global is None:
        db = next(get_db())
        _repo_global = RepoRevisiones(db)
    return _repo_global


def registrar_revision(
    entidad_tipo: str,
    entidad_id: int,
    usuario: str,
    estado: str,
    comentario: str = "",
) -> Revision:
    return _get_global_repo().registrar(entidad_tipo, entidad_id, usuario, estado, comentario)


def listar_revisiones(entidad_tipo: str, entidad_id: int) -> list[Revision]:
    return _get_global_repo().listar(entidad_tipo, entidad_id)


def obtener_ultima_revision(entidad_tipo: str, entidad_id: int) -> Revision | None:
    return _get_global_repo().obtener_ultima(entidad_tipo, entidad_id)


def _limpiar_revisiones() -> None:
    """Solo para tests. Limpia la tabla de revisiones en DB."""
    global _repo_global
    _repo_global = None
    try:
        db = next(get_db())
        db.query(DBRevision).delete()
        db.commit()
    except Exception:
        pass
