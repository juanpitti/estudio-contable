"""API de clientes — cartera mínima del estudio (Etapa 1).

Repositorio SQLAlchemy inyectable (Depends): PostgreSQL en producción,
SQLite en tests, sin cambios en los endpoints.
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.auth import requerir_rol, usuario_actual
from app.database import get_db
from app.models import Cliente, ClienteIn
from app.models_db import DBCliente

router = APIRouter(prefix="/clientes", tags=["clientes"])


class CuitDuplicado(Exception):
    pass


class RepoClientes:
    def __init__(self, db: Session) -> None:
        self._db = db

    def crear(self, datos: ClienteIn) -> Cliente:
        if self._db.query(DBCliente).filter_by(cuit=datos.cuit).first():
            raise CuitDuplicado(datos.cuit)
        db_cli = DBCliente(
            cuit=datos.cuit,
            razon_social=datos.razon_social,
            condicion_iva=datos.condicion_iva,
        )
        self._db.add(db_cli)
        self._db.commit()
        self._db.refresh(db_cli)
        return Cliente(id=db_cli.id, **datos.model_dump())

    def listar(self) -> list[Cliente]:
        return [
            Cliente(id=c.id, cuit=c.cuit, razon_social=c.razon_social, condicion_iva=c.condicion_iva)
            for c in self._db.query(DBCliente).all()
        ]

    def obtener(self, cliente_id: int) -> Cliente | None:
        c = self._db.query(DBCliente).filter_by(id=cliente_id).first()
        if not c:
            return None
        return Cliente(id=c.id, cuit=c.cuit, razon_social=c.razon_social, condicion_iva=c.condicion_iva)


def get_repo(db: Session = Depends(get_db)) -> RepoClientes:
    return RepoClientes(db)


@router.post("", status_code=201, response_model=Cliente)
def crear_cliente(
    datos: ClienteIn,
    repo: RepoClientes = Depends(get_repo),
    _usuario: dict = Depends(requerir_rol("owner", "senior")),
) -> Cliente:
    try:
        return repo.crear(datos)
    except CuitDuplicado:
        raise HTTPException(status_code=409, detail=f"CUIT ya registrado: {datos.cuit}")


@router.get("", response_model=list[Cliente])
def listar_clientes(
    repo: RepoClientes = Depends(get_repo),
    _usuario: dict = Depends(usuario_actual),
) -> list[Cliente]:
    return repo.listar()


@router.get("/{cliente_id}", response_model=Cliente)
def obtener_cliente(
    cliente_id: int,
    repo: RepoClientes = Depends(get_repo),
    _usuario: dict = Depends(usuario_actual),
) -> Cliente:
    cliente = repo.obtener(cliente_id)
    if cliente is None:
        raise HTTPException(status_code=404, detail="Cliente no encontrado")
    return cliente
