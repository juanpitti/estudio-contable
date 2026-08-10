"""API de comprobantes IVA + pre-liquidación mensual (Etapa 2).

Repositorio SQLAlchemy inyectable. PostgreSQL en producción, SQLite en tests.
"""

from datetime import date, datetime, timezone
from decimal import Decimal
from typing import Literal

from fastapi import APIRouter, Depends, HTTPException, Query, Response
from pydantic import BaseModel, field_validator
from sqlalchemy.orm import Session

from app.api.clientes import RepoClientes, get_repo
from app.auth import requerir_rol, usuario_actual
from app.database import get_db
from app.iva.alertas import analizar_alertas
from app.iva.calculadora import liquidacion_iva
from app.iva.comprobante import AlicuotaLinea, ComprobanteIva
from app.iva.papeles import generar_papel_trabajo
from app.models_db import DBComprobante, DBLineaAlicuota

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
    def __init__(self, db: Session) -> None:
        self._db = db

    def crear(self, cliente_id: int, datos: ComprobanteIn, confirmado_por: str) -> ComprobanteIva:
        db_comp = DBComprobante(
            cliente_id=cliente_id,
            tipo=datos.tipo,
            fecha=date.fromisoformat(datos.fecha),
            confirmado_por=confirmado_por,
            confirmado_en=datetime.now(timezone.utc),
        )
        self._db.add(db_comp)
        self._db.flush()  # para obtener db_comp.id

        for l in datos.lineas:
            db_linea = DBLineaAlicuota(
                comprobante_id=db_comp.id,
                alicuota=l.alicuota,
                neto=l.neto,
                iva=l.iva,
            )
            self._db.add(db_linea)

        self._db.commit()
        self._db.refresh(db_comp)
        return self._to_domain(db_comp)

    def de_cliente(self, cliente_id: int) -> list[ComprobanteIva]:
        comps = self._db.query(DBComprobante).filter_by(cliente_id=cliente_id).all()
        return [self._to_domain(c) for c in comps]

    def historial_saldos_favor(self, cliente_id: int, periodos: list[str]) -> list[Decimal]:
        resultados = []
        for periodo in periodos:
            comps = self.de_cliente(cliente_id)
            comps_periodo = [c for c in comps if c.periodo == periodo]
            liq = liquidacion_iva(
                [c for c in comps_periodo if c.tipo == "venta"],
                [c for c in comps_periodo if c.tipo == "compra"],
                Decimal("0"),
            )
            resultados.append(liq.saldo_a_favor_final)
        return resultados

    def _to_domain(self, db_comp: DBComprobante) -> ComprobanteIva:
        def _norm(d: Decimal) -> Decimal:
            s = str(d)
            if "." in s:
                s = s.rstrip("0").rstrip(".")
            return Decimal(s) if s else Decimal("0")

        return ComprobanteIva(
            id=db_comp.id,
            cliente_id=db_comp.cliente_id,
            tipo=db_comp.tipo,
            fecha=db_comp.fecha,
            lineas=[
                AlicuotaLinea(_norm(l.alicuota), _norm(l.neto), _norm(l.iva))
                for l in db_comp.lineas
            ],
            confirmado_por=db_comp.confirmado_por,
            confirmado_en=db_comp.confirmado_en,
        )


def get_repo_comprobantes(db: Session = Depends(get_db)) -> RepoComprobantes:
    return RepoComprobantes(db)


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
    año, mes = periodo.split("-")
    periodos_previos = []
    for i in range(1, 12):
        m = int(mes) - i
        y = int(año)
        while m <= 0:
            m += 12
            y -= 1
        periodos_previos.append(f"{y:04d}-{m:02d}")
    historial = repo.historial_saldos_favor(cliente_id, periodos_previos)
    alertas = analizar_alertas(liq, historial)
    return {
        "periodo": periodo,
        "debito": {str(a): str(t) for a, t in liq.debito.items()},
        "credito": {str(a): str(t) for a, t in liq.credito.items()},
        "saldo_favor_anterior": str(liq.saldo_favor_anterior),
        "saldo_a_pagar": str(liq.saldo_a_pagar),
        "saldo_a_favor_final": str(liq.saldo_a_favor_final),
        "comprobantes_incluidos": [c.id for c in comps],
        "alertas": [{"nivel": a.nivel, "codigo": a.codigo, "mensaje": a.mensaje} for a in alertas],
    }


@router.get("/iva/{periodo}/papel-trabajo")
def descargar_papel_trabajo(
    cliente_id: int,
    periodo: str,
    saldo_favor_anterior: Decimal = Query(default=Decimal("0")),
    repo: RepoComprobantes = Depends(get_repo_comprobantes),
    repo_cli: RepoClientes = Depends(get_repo),
    _usuario: dict = Depends(usuario_actual),
):
    _verificar_cliente(cliente_id, repo_cli)
    comps = [c for c in repo.de_cliente(cliente_id) if c.periodo == periodo]
    liq = liquidacion_iva(
        [c for c in comps if c.tipo == "venta"],
        [c for c in comps if c.tipo == "compra"],
        saldo_favor_anterior,
    )
    data = generar_papel_trabajo(liq, comps, periodo)
    return Response(
        content=data,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": f'attachment; filename="papel-trabajo-{periodo}.xlsx"'},
    )
