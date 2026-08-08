"""API de comprobantes IVA + pre-liquidación mensual (Etapa 2).

La ingesta es SIEMPRE por confirmación humana (bitácora Ley 20.488):
queda registrado quién confirmó y cuándo. La liquidación devuelve el
desglose por alícuota y los comprobantes incluidos: cada número dice
de dónde salió (Plan v4 regla 6).
"""

from datetime import datetime, timezone
from decimal import Decimal
from typing import Literal

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, field_validator

from app.api.clientes import RepoClientes, get_repo
from app.auth import requerir_rol, usuario_actual
from app.iva.calculadora import liquidacion_iva
from app.iva.comprobante import AlicuotaLinea, ComprobanteIva

router = APIRouter(prefix="/clientes/{cliente_id}", tags=["comprobantes"])

ALICUOTAS_VALIDAS = {Decimal("0.21"), Decimal("0.105"), Decimal("0.27")}


class AlicuotaLineaIn(BaseModel):
    alicuota: Decimal
    neto: Decimal
    iva: Decimal

    @field_validator("alicuota")
    @classmethod
    def _alicuota_valida(cls, v: Decimal) -> Decimal:
        if v not in ALICUOTAS_VALIDAS:
            raise ValueError("Alícuota inválida (válidas: 0.21, 0.105, 0.27)")
        return v


class ComprobanteIn(BaseModel):
    tipo: Literal["venta", "compra"]
    fecha: str  # YYYY-MM-DD
    lineas: list[AlicuotaLineaIn]


class RepoComprobantes:
    def __init__(self) -> None:
        self._datos: dict[int, ComprobanteIva] = {}
        self._seq = 0

    def crear(self, cliente_id: int, datos: ComprobanteIn, confirmado_por: str) -> ComprobanteIva:
        from datetime import date

        self._seq += 1
        comp = ComprobanteIva(
            id=self._seq,
            cliente_id=cliente_id,
            tipo=datos.tipo,
            fecha=date.fromisoformat(datos.fecha),
            lineas=[AlicuotaLinea(l.alicuota, l.neto, l.iva) for l in datos.lineas],
            confirmado_por=confirmado_por,
            confirmado_en=datetime.now(timezone.utc),
        )
        self._datos[comp.id] = comp
        return comp

    def de_cliente(self, cliente_id: int) -> list[ComprobanteIva]:
        return [c for c in self._datos.values() if c.cliente_id == cliente_id]


_repo = RepoComprobantes()


def get_repo_comprobantes() -> RepoComprobantes:
    return _repo


def _serializar(comp: ComprobanteIva) -> dict:
    return {
        "id": comp.id,
        "cliente_id": comp.cliente_id,
        "tipo": comp.tipo,
        "fecha": comp.fecha.isoformat(),
        "lineas": [
            {"alicuota": str(l.alicuota), "neto": str(l.neto), "iva": str(l.iva)}
            for l in comp.lineas
        ],
        "confirmado_por": comp.confirmado_por,
        "confirmado_en": comp.confirmado_en.isoformat() if comp.confirmado_en else None,
    }


def _verificar_cliente(cliente_id: int, repo_cli: RepoClientes) -> None:
    if repo_cli.obtener(cliente_id) is None:
        raise HTTPException(status_code=404, detail="Cliente no encontrado")


@router.post("/comprobantes", status_code=201)
def ingresar_comprobante(
    cliente_id: int,
    datos: ComprobanteIn,
    repo: RepoComprobantes = Depends(get_repo_comprobantes),
    repo_cli: RepoClientes = Depends(get_repo),
    usuario: dict = Depends(requerir_rol("owner", "senior")),
) -> dict:
    _verificar_cliente(cliente_id, repo_cli)
    comp = repo.crear(cliente_id, datos, confirmado_por=usuario["sub"])
    return _serializar(comp)


@router.get("/comprobantes")
def listar_comprobantes(
    cliente_id: int,
    repo: RepoComprobantes = Depends(get_repo_comprobantes),
    repo_cli: RepoClientes = Depends(get_repo),
    _usuario: dict = Depends(usuario_actual),
) -> list[dict]:
    _verificar_cliente(cliente_id, repo_cli)
    return [_serializar(c) for c in repo.de_cliente(cliente_id)]


@router.get("/iva/{periodo}")
def liquidacion_del_periodo(
    cliente_id: int,
    periodo: str,
    saldo_favor_anterior: Decimal = Query(default=Decimal("0")),
    repo: RepoComprobantes = Depends(get_repo_comprobantes),
    repo_cli: RepoClientes = Depends(get_repo),
    _usuario: dict = Depends(usuario_actual),
) -> dict:
    _verificar_cliente(cliente_id, repo_cli)
    comps = [c for c in repo.de_cliente(cliente_id) if c.periodo == periodo]
    liq = liquidacion_iva(
        [c for c in comps if c.tipo == "venta"],
        [c for c in comps if c.tipo == "compra"],
        saldo_favor_anterior,
    )
    return {
        "periodo": periodo,
        "debito": {str(a): str(t) for a, t in liq.debito.items()},
        "credito": {str(a): str(t) for a, t in liq.credito.items()},
        "saldo_favor_anterior": str(liq.saldo_favor_anterior),
        "saldo_a_pagar": str(liq.saldo_a_pagar),
        "saldo_a_favor_final": str(liq.saldo_a_favor_final),
        "comprobantes_incluidos": [c.id for c in comps],
    }
