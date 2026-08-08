"""API de clientes — cartera mínima del estudio (Etapa 1).

Repositorio en memoria detrás de una interfaz inyectable (Depends):
PostgreSQL lo reemplaza en la iteración con DB sin tocar los endpoints.
"""

from fastapi import APIRouter, Depends, HTTPException

from app.auth import requerir_rol, usuario_actual
from app.models import Cliente, ClienteIn

router = APIRouter(prefix="/clientes", tags=["clientes"])


class CuitDuplicado(Exception):
    pass


class RepoClientes:
    def __init__(self) -> None:
        self._datos: dict[int, Cliente] = {}
        self._seq = 0

    def crear(self, datos: ClienteIn) -> Cliente:
        if any(c.cuit == datos.cuit for c in self._datos.values()):
            raise CuitDuplicado(datos.cuit)
        self._seq += 1
        cliente = Cliente(id=self._seq, **datos.model_dump())
        self._datos[cliente.id] = cliente
        return cliente

    def listar(self) -> list[Cliente]:
        return list(self._datos.values())

    def obtener(self, cliente_id: int) -> Cliente | None:
        return self._datos.get(cliente_id)


_repo = RepoClientes()


def get_repo() -> RepoClientes:
    return _repo


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
