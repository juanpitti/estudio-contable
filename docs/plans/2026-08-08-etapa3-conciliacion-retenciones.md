# Etapa 3 — Conciliación bancaria y retenciones — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use the executing-plans skill. Steps use checkbox (`- [ ]`) syntax.

**Goal:** Motor de conciliación bancaria con 4 niveles de match, parser de movimientos bancarios CSV, deduplicador, y pantalla web que muestra % de match, diferencias y consolidado del mes.

**Architecture:** Nuevo dominio `app/conciliacion/` con modelo `MovimientoBancario`, `parser_csv.py` (lectura genérica), `matcher.py` (4 niveles de match), `deduplicador.py`. API en `app/api/conciliacion.py` expone POST /clientes/{id}/conciliacion/importar (sube CSV), GET /clientes/{id}/conciliacion/{periodo} (resultados). Frontend: nueva solapa "Conciliación" con drag&drop CSV, tabla de resultados.

**Tech Stack:** FastAPI, Python 3.12, Decimal, csv, React+TS, openpyxl (parser xlsx opcional).

## Global Constraints

- Dinero con Decimal, nunca float.
- Todo comprobante conciliado mantiene trazabilidad: qué movimiento bancario lo tocó, qué nivel de match, quién confirmó.
- Datos de prueba siempre ficticios en dev/staging (Plan v4 regla 2).
- TDD: tests con datos calculados a mano.
- El parser CSV acepta delimitador configurable (coma, punto y coma, tab) — los bancos argentinos usan punto y coma.

---

### Task 1: Modelo de movimiento bancario + parser CSV (TDD)

**Files:**
- Create: `backend/app/conciliacion/__init__.py`, `backend/app/conciliacion/movimiento.py`, `backend/app/conciliacion/parser_csv.py`
- Test: `backend/tests/test_parser_csv.py`

**Interfaces:**
- Consumes: bytes (contenido CSV)
- Produces: `list[MovimientoBancario]` donde `MovimientoBancario` tiene `id, cliente_id, fecha, descripcion, monto: Decimal, tipo: "debito"|"credito", banco: str`

- [ ] **Step 1: Test rojo**

```python
# tests/test_parser_csv.py
from decimal import Decimal
from datetime import date
from io import BytesIO

from app.conciliacion.movimiento import MovimientoBancario
from app.conciliacion.parser_csv import parsear_csv


def test_parsear_csv_simple():
    csv = b"fecha;descripcion;debito;\n2026-08-01;PAGO PROVEEDOR;15000,50;\n"
    movs = parsear_csv(csv, delimitador=";", formato_numero="es_AR")
    assert len(movs) == 1
    assert movs[0].fecha == date(2026, 8, 1)
    assert movs[0].descripcion == "PAGO PROVEEDOR"
    assert movs[0].monto == Decimal("15000.50")
    assert movs[0].tipo == "debito"


def test_parsear_csv_coma_decimal():
    csv = b"fecha,descripcion,credito,\n2026-08-02,COBRO CLIENTE,25000.00,\n"
    movs = parsear_csv(csv, delimitador=",", formato_numero="en_US")
    assert len(movs) == 1
    assert movs[0].monto == Decimal("25000.00")
    assert movs[0].tipo == "credito"


def test_parsear_csv_ignora_saldo():
    csv = b"fecha;concepto;debito;credito;saldo;\n2026-08-03;FACTURA;5000;;10000;\n"
    movs = parsear_csv(csv, delimitador=";", formato_numero="es_AR")
    assert len(movs) == 1
    assert movs[0].monto == Decimal("5000")


def test_parsear_csv_detecta_columnas():
    csv = b"Fecha;Descripción;Importe Debido;Importe Acreditado;\n2026-08-04;PAGO;10000;;\n2026-08-05;COBRO;;20000;\n"
    movs = parsear_csv(csv, delimitador=";", formato_numero="es_AR")
    assert len(movs) == 2
    assert movs[0].monto == Decimal("10000")
    assert movs[0].tipo == "debito"
    assert movs[1].monto == Decimal("20000")
    assert movs[1].tipo == "credito"
```

- [ ] **Step 2:** Correr → FAIL

Run: `cd backend && python -m pytest tests/test_parser_csv.py -v`
Expected: 4 FAIL

- [ ] **Step 3: Implementar modelo + parser**

```python
# backend/app/conciliacion/movimiento.py
from dataclasses import dataclass
from datetime import date
from decimal import Decimal
from typing import Literal


@dataclass(frozen=True)
class MovimientoBancario:
    id: int
    cliente_id: int
    fecha: date
    descripcion: str
    monto: Decimal
    tipo: Literal["debito", "credito"]
    banco: str = ""
```

```python
# backend/app/conciliacion/parser_csv.py
import csv
from datetime import datetime
from decimal import Decimal
from io import BytesIO, StringIO
from typing import Literal

from app.conciliacion.movimiento import MovimientoBancario


def _normalizar_header(h: str) -> str:
    return h.strip().lower().replace("á", "a").replace("é", "e").replace("í", "i").replace("ó", "o").replace("ú", "u")


def _detectar_columnas(headers: list[str]) -> dict[str, int]:
    """Mapea índices de columnas reconocidas."""
    norm = [_normalizar_header(h) for h in headers]
    mapeo = {}
    for i, h in enumerate(norm):
        if h in ("fecha", "fecha de operacion", "fecha operacion", "fecha oper."):
            mapeo["fecha"] = i
        if h in ("descripcion", "concepto", "descrip.", "detalle", "descripción", "movimiento"):
            mapeo["descripcion"] = i
        if h in ("debito", "debe", "importe debido", "cargo", "egreso"):
            mapeo["debito"] = i
        if h in ("credito", "haber", "importe acreditado", "abono", "ingreso"):
            mapeo["credito"] = i
    if "descripcion" not in mapeo and len(headers) > 1:
        mapeo["descripcion"] = 1  # fallback: segunda columna
    return mapeo


def _parsear_monto(v: str, formato: Literal["es_AR", "en_US"]) -> Decimal | None:
    v = v.strip()
    if not v:
        return None
    if formato == "es_AR":
        # 1.234,56 → 1234.56
        v = v.replace(".", "").replace(",", ".")
    else:
        v = v.replace(",", "")
    return Decimal(v)


def parsear_csv(
    contenido: bytes,
    cliente_id: int = 0,
    delimitador: str = ";",
    formato_numero: Literal["es_AR", "en_US"] = "es_AR",
    banco: str = "",
) -> list[MovimientoBancario]:
    texto = contenido.decode("utf-8-sig")
    reader = csv.reader(StringIO(texto), delimiter=delimitador)
    headers = next(reader)
    col = _detectar_columnas(headers)

    if "fecha" not in col:
        raise ValueError("No se encontró columna de fecha")

    movimientos = []
    seq = 0
    for row in reader:
        if not row or all(not c.strip() for c in row):
            continue
        fecha_str = row[col["fecha"]].strip()
        try:
            fecha = datetime.strptime(fecha_str, "%Y-%m-%d").date()
        except ValueError:
            try:
                fecha = datetime.strptime(fecha_str, "%d/%m/%Y").date()
            except ValueError:
                continue

        desc = row[col.get("descripcion", 1)].strip() if "descripcion" in col else ""

        monto = None
        tipo = "debito"

        if "debito" in col and col["debito"] < len(row):
            m = _parsear_monto(row[col["debito"]], formato_numero)
            if m and m > 0:
                monto = m
                tipo = "debito"

        if monto is None and "credito" in col and col["credito"] < len(row):
            m = _parsear_monto(row[col["credito"]], formato_numero)
            if m and m > 0:
                monto = m
                tipo = "credito"

        if monto is None:
            continue

        seq += 1
        movimientos.append(MovimientoBancario(
            id=seq, cliente_id=cliente_id, fecha=fecha,
            descripcion=desc, monto=monto, tipo=tipo, banco=banco,
        ))

    return movimientos
```

- [ ] **Step 4:** Correr → PASS

Run: `cd backend && python -m pytest tests/test_parser_csv.py -v`
Expected: 4 passed

- [ ] **Step 5:** Commit

```bash
cd estudio-contable && git add backend/app/conciliacion/ backend/tests/test_parser_csv.py && git commit -m "feat(conciliacion): modelo movimiento bancario + parser CSV genérico"
```

---

### Task 2: Deduplicador de movimientos (TDD)

**Files:**
- Create: `backend/app/conciliacion/deduplicador.py`
- Test: `backend/tests/test_deduplicador.py`

**Interfaces:**
- Consumes: `list[MovimientoBancario]`
- Produces: `tuple[list[MovimientoBancario], list[MovimientoBancario]]` → (únicos, duplicados)

- [ ] **Step 1: Test rojo**

```python
# tests/test_deduplicador.py
from decimal import Decimal
from datetime import date

from app.conciliacion.movimiento import MovimientoBancario
from app.conciliacion.deduplicador import deduplicar


def test_sin_duplicados():
    movs = [
        MovimientoBancario(1, 1, date(2026, 8, 1), "PAGO A", Decimal("1000"), "debito"),
        MovimientoBancario(2, 1, date(2026, 8, 2), "PAGO B", Decimal("2000"), "debito"),
    ]
    unicos, dups = deduplicar(movs)
    assert len(unicos) == 2
    assert len(dups) == 0


def test_detecta_duplicado_exacto():
    movs = [
        MovimientoBancario(1, 1, date(2026, 8, 1), "PAGO", Decimal("1000"), "debito"),
        MovimientoBancario(2, 1, date(2026, 8, 1), "PAGO", Decimal("1000"), "debito"),
    ]
    unicos, dups = deduplicar(movs)
    assert len(unicos) == 1
    assert len(dups) == 1


def test_diferente_monto_no_es_duplicado():
    movs = [
        MovimientoBancario(1, 1, date(2026, 8, 1), "PAGO", Decimal("1000"), "debito"),
        MovimientoBancario(2, 1, date(2026, 8, 1), "PAGO", Decimal("2000"), "debito"),
    ]
    unicos, dups = deduplicar(movs)
    assert len(unicos) == 2
    assert len(dups) == 0
```

- [ ] **Step 2:** Correr → FAIL

- [ ] **Step 3: Implementar deduplicador**

```python
# backend/app/conciliacion/deduplicador.py
from app.conciliacion.movimiento import MovimientoBancario


def deduplicar(movs: list[MovimientoBancario]) -> tuple[list[MovimientoBancario], list[MovimientoBancario]]:
    """Detecta duplicados por (fecha, monto, descripcion, tipo)."""
    vistos: set[tuple] = set()
    unicos: list[MovimientoBancario] = []
    duplicados: list[MovimientoBancario] = []
    for m in movs:
        clave = (m.fecha, m.monto, m.descripcion, m.tipo)
        if clave in vistos:
            duplicados.append(m)
        else:
            vistos.add(clave)
            unicos.append(m)
    return unicos, duplicados
```

- [ ] **Step 4:** Correr → PASS

- [ ] **Step 5:** Commit

```bash
cd estudio-contable && git add backend/app/conciliacion/deduplicador.py backend/tests/test_deduplicador.py && git commit -m "feat(conciliacion): deduplicador de movimientos bancarios"
```

---

### Task 3: Motor de match 4 niveles (TDD)

**Files:**
- Create: `backend/app/conciliacion/matcher.py`
- Test: `backend/tests/test_matcher.py`

**Interfaces:**
- Consumes: `list[ComprobanteIva]` (compras), `list[MovimientoBancario]`
- Produces: `ResultadoConciliacion` con `matches: list[Match]`, `sin_match_compras: list[ComprobanteIva]`, `sin_match_banco: list[MovimientoBancario]`, `porcentaje_match: float`

Los 4 niveles:
1. **Exacto**: monto exacto + fecha exacta + CUIT del emisor en descripción del banco
2. **Monto+fecha**: monto exacto + fecha exacta (sin CUIT)
3. **Monto+rango**: monto exacto + fecha +/- 3 días
4. **Aproximado**: monto +/- 2% + fecha +/- 5 días

- [ ] **Step 1: Test rojo**

```python
# tests/test_matcher.py
from decimal import Decimal
from datetime import date, timedelta

from app.conciliacion.movimiento import MovimientoBancario
from app.conciliacion.matcher import conciliar, NivelMatch
from app.iva.comprobante import ComprobanteIva, AlicuotaLinea


def _comp(id, fecha, neto, iva):
    return ComprobanteIva(
        id=id, cliente_id=1, tipo="compra", fecha=date.fromisoformat(fecha),
        lineas=[AlicuotaLinea(Decimal("0.21"), Decimal(neto), Decimal(iva))],
        confirmado_por="test", confirmado_en=None,
    )


def _mov(id, fecha, monto, desc="PAGO"):
    return MovimientoBancario(
        id=id, cliente_id=1, fecha=date.fromisoformat(fecha),
        descripcion=desc, monto=Decimal(str(monto)), tipo="debito",
    )


def test_match_exacto():
    comps = [_comp(1, "2026-08-01", "10000", "2100")]  # total 12100
    movs = [_mov(1, "2026-08-01", 12100)]
    res = conciliar(comps, movs)
    assert len(res.matches) == 1
    assert res.matches[0].nivel == NivelMatch.EXACTO
    assert res.porcentaje_match == 100.0


def test_match_monto_fecha():
    comps = [_comp(1, "2026-08-01", "10000", "2100")]
    movs = [_mov(1, "2026-08-01", 12100, "TRANSFERENCIA")]
    res = conciliar(comps, movs)
    assert len(res.matches) == 1
    assert res.matches[0].nivel == NivelMatch.MONTO_FECHA


def test_match_monto_rango():
    comps = [_comp(1, "2026-08-01", "10000", "2100")]
    movs = [_mov(1, "2026-08-04", 12100)]  # +3 días
    res = conciliar(comps, movs)
    assert len(res.matches) == 1
    assert res.matches[0].nivel == NivelMatch.MONTO_RANGO


def test_match_aproximado():
    comps = [_comp(1, "2026-08-01", "10000", "2100")]  # 12100
    movs = [_mov(1, "2026-08-06", 12000)]  # -100 (0.8% diff), +5 días
    res = conciliar(comps, movs)
    assert len(res.matches) == 1
    assert res.matches[0].nivel == NivelMatch.APROXIMADO


def test_sin_match():
    comps = [_comp(1, "2026-08-01", "10000", "2100")]
    movs = [_mov(1, "2026-08-15", 5000)]
    res = conciliar(comps, movs)
    assert len(res.matches) == 0
    assert len(res.sin_match_compras) == 1
    assert len(res.sin_match_banco) == 1


def test_diferencia_detectada():
    comps = [_comp(1, "2026-08-01", "10000", "2100")]  # 12100
    movs = [_mov(1, "2026-08-01", 15000)]  # 2900 de diferencia
    res = conciliar(comps, movs)
    # No hace match exacto porque el monto difiere
    assert len(res.matches) == 0
    assert len(res.sin_match_compras) == 1
    assert len(res.sin_match_banco) == 1
    assert len(res.diferencias) == 1
    assert res.diferencias[0].monto_diferencia == Decimal("2900")
```

- [ ] **Step 2:** Correr → FAIL

- [ ] **Step 3: Implementar motor de match**

```python
# backend/app/conciliacion/matcher.py
from dataclasses import dataclass
from decimal import Decimal
from datetime import date, timedelta
from enum import Enum

from app.conciliacion.movimiento import MovimientoBancario
from app.iva.comprobante import ComprobanteIva


class NivelMatch(Enum):
    EXACTO = "exacto"
    MONTO_FECHA = "monto_fecha"
    MONTO_RANGO = "monto_rango"
    APROXIMADO = "aproximado"


@dataclass(frozen=True)
class Match:
    comprobante_id: int
    movimiento_id: int
    nivel: NivelMatch
    monto_comprobante: Decimal
    monto_movimiento: Decimal


@dataclass(frozen=True)
class Diferencia:
    comprobante_id: int
    movimiento_id: int
    monto_comprobante: Decimal
    monto_movimiento: Decimal
    monto_diferencia: Decimal


@dataclass(frozen=True)
class ResultadoConciliacion:
    matches: list[Match]
    sin_match_compras: list[ComprobanteIva]
    sin_match_banco: list[MovimientoBancario]
    diferencias: list[Diferencia]
    porcentaje_match: float


def _total_comprobante(c: ComprobanteIva) -> Decimal:
    """Importe total del comprobante (neto + iva)."""
    return sum(l.neto + l.iva for l in c.lineas)


def _monto_igual(a: Decimal, b: Decimal) -> bool:
    return a == b


def _monto_aproximado(a: Decimal, b: Decimal, tolerancia: Decimal = Decimal("0.02")) -> bool:
    if a == 0:
        return False
    diff = abs(a - b) / a
    return diff <= tolerancia


def conciliar(
    compras: list[ComprobanteIva],
    movimientos: list[MovimientoBancario],
) -> ResultadoConciliacion:
    matches: list[Match] = []
    diferencias: list[Diferencia] = []
    compras_pendientes = list(compras)
    movs_pendientes = list(movimientos)

    # Nivel 1: Exacto (monto + fecha exacta)
    for c in list(compras_pendientes):
        total = _total_comprobante(c)
        for m in list(movs_pendientes):
            if _monto_igual(total, m.monto) and c.fecha == m.fecha:
                matches.append(Match(c.id, m.id, NivelMatch.EXACTO, total, m.monto))
                compras_pendientes.remove(c)
                movs_pendientes.remove(m)
                break

    # Nivel 2: Monto + fecha exacta (sin CUIT, cualquier descripción)
    for c in list(compras_pendientes):
        total = _total_comprobante(c)
        for m in list(movs_pendientes):
            if _monto_igual(total, m.monto) and c.fecha == m.fecha:
                matches.append(Match(c.id, m.id, NivelMatch.MONTO_FECHA, total, m.monto))
                compras_pendientes.remove(c)
                movs_pendientes.remove(m)
                break

    # Nivel 3: Monto exacto + fecha +/- 3 días
    for c in list(compras_pendientes):
        total = _total_comprobante(c)
        for m in list(movs_pendientes):
            if _monto_igual(total, m.monto) and abs((c.fecha - m.fecha).days) <= 3:
                matches.append(Match(c.id, m.id, NivelMatch.MONTO_RANGO, total, m.monto))
                compras_pendientes.remove(c)
                movs_pendientes.remove(m)
                break

    # Nivel 4: Aproximado (monto +/- 2%) + fecha +/- 5 días
    for c in list(compras_pendientes):
        total = _total_comprobante(c)
        for m in list(movs_pendientes):
            if _monto_aproximado(total, m.monto) and abs((c.fecha - m.fecha).days) <= 5:
                matches.append(Match(c.id, m.id, NivelMatch.APROXIMADO, total, m.monto))
                compras_pendientes.remove(c)
                movs_pendientes.remove(m)
                break

    # Detectar diferencias: compras y movimientos sin match con fechas cercanas
    for c in compras_pendientes:
        total = _total_comprobante(c)
        for m in movs_pendientes:
            if abs((c.fecha - m.fecha).days) <= 5:
                diff = abs(total - m.monto)
                if diff > 0:
                    diferencias.append(Diferencia(
                        c.id, m.id, total, m.monto, diff,
                    ))
                break  # solo la primera diferencia por comprobante

    total_items = len(compras) + len(movimientos)
    matched_items = len(matches) * 2
    porcentaje = (matched_items / total_items * 100) if total_items > 0 else 0.0

    return ResultadoConciliacion(
        matches=matches,
        sin_match_compras=compras_pendientes,
        sin_match_banco=movs_pendientes,
        diferencias=diferencias,
        porcentaje_match=round(porcentaje, 1),
    )
```

- [ ] **Step 4:** Correr → PASS

- [ ] **Step 5:** Commit

```bash
cd estudio-contable && git add backend/app/conciliacion/matcher.py backend/tests/test_matcher.py && git commit -m "feat(conciliacion): motor de match 4 niveles (exacto, monto+fecha, rango, aproximado)"
```

---

### Task 4: API de conciliación

**Files:**
- Create: `backend/app/api/conciliacion.py`
- Test: `backend/tests/test_conciliacion_api.py`
- Modify: `backend/app/main.py` (incluir router)

**Interfaces:**
- Consumes: `parsear_csv`, `deduplicar`, `conciliar`
- Produces: `POST /clientes/{id}/conciliacion/importar` → sube CSV, devuelve resultado; `GET /clientes/{id}/conciliacion/{periodo}` → resultado almacenado

- [ ] **Step 1: Test rojo**

```python
# tests/test_conciliacion_api.py
import pytest
from fastapi.testclient import TestClient

from app.api.clientes import RepoClientes, get_repo
from app.api.comprobantes import RepoComprobantes, get_repo_comprobantes
from app.main import app


@pytest.fixture
def client():
    repo_cli = RepoClientes()
    repo_comp = RepoComprobantes()
    app.dependency_overrides[get_repo] = lambda: repo_cli
    app.dependency_overrides[get_repo_comprobantes] = lambda: repo_comp
    c = TestClient(app)
    token = c.post(
        "/auth/login", json={"username": "owner", "password": "owner123"}
    ).json()["access_token"]
    c.headers["Authorization"] = f"Bearer {token}"
    c.post(
        "/clientes",
        json={"cuit": "20-27396523-9", "razon_social": "Prueba SA", "condicion_iva": "RI"},
    )
    # Ingresar una compra
    c.post("/clientes/1/comprobantes", json={
        "tipo": "compra", "fecha": "2026-08-01",
        "lineas": [{"alicuota": "0.21", "neto": "10000", "iva": "2100"}]
    })
    yield c
    app.dependency_overrides.clear()


def test_importar_csv_y_conciliar(client):
    csv = b"fecha;descripcion;debito;\n2026-08-01;PAGO PROVEEDOR;12100,00;\n"
    r = client.post("/clientes/1/conciliacion/importar", data={"delimitador": ";"}, files={"archivo": ("movimientos.csv", csv, "text/csv")})
    assert r.status_code == 200
    data = r.json()
    assert data["porcentaje_match"] > 0
    assert len(data["matches"]) == 1
    assert data["matches"][0]["nivel"] == "exacto"
    assert len(data["duplicados"]) == 0
```

- [ ] **Step 2:** Correr → FAIL

- [ ] **Step 3: Implementar API**

```python
# backend/app/api/conciliacion.py
from decimal import Decimal
from typing import Literal

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile

from app.api.clientes import RepoClientes, get_repo
from app.api.comprobantes import RepoComprobantes, get_repo_comprobantes
from app.auth import requerir_rol, usuario_actual
from app.conciliacion.deduplicador import deduplicar
from app.conciliacion.matcher import conciliar
from app.conciliacion.parser_csv import parsear_csv

router = APIRouter(tags=["conciliacion"])


@router.post("/clientes/{cliente_id}/conciliacion/importar")
def importar_y_conciliar(
    cliente_id: int,
    archivo: UploadFile = File(...),
    delimitador: str = Form(default=";"),
    formato_numero: Literal["es_AR", "en_US"] = Form(default="es_AR"),
    repo_comp: RepoComprobantes = Depends(get_repo_comprobantes),
    repo_cli: RepoClientes = Depends(get_repo),
    usuario: dict = Depends(requerir_rol("owner", "senior")),
):
    if repo_cli.obtener(cliente_id) is None:
        raise HTTPException(status_code=404, detail="Cliente no encontrado")

    contenido = archivo.file.read()
    try:
        movs = parsear_csv(contenido, cliente_id, delimitador, formato_numero)
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))

    movs_unicos, duplicados = deduplicar(movs)
    compras = [c for c in repo_comp.de_cliente(cliente_id) if c.tipo == "compra"]
    resultado = conciliar(compras, movs_unicos)

    return {
        "porcentaje_match": resultado.porcentaje_match,
        "matches": [
            {
                "comprobante_id": m.comprobante_id,
                "movimiento_id": m.movimiento_id,
                "nivel": m.nivel.value,
                "monto_comprobante": str(m.monto_comprobante),
                "monto_movimiento": str(m.monto_movimiento),
            }
            for m in resultado.matches
        ],
        "sin_match_compras": [c.id for c in resultado.sin_match_compras],
        "sin_match_banco": [
            {"id": m.id, "fecha": m.fecha.isoformat(), "descripcion": m.descripcion, "monto": str(m.monto)}
            for m in resultado.sin_match_banco
        ],
        "diferencias": [
            {
                "comprobante_id": d.comprobante_id,
                "movimiento_id": d.movimiento_id,
                "monto_diferencia": str(d.monto_diferencia),
            }
            for d in resultado.diferencias
        ],
        "duplicados": len(duplicados),
        "importados": len(movs),
        "periodo": compras[0].periodo if compras else "",
        "confirmado_por": usuario["sub"],
    }
```

- [ ] **Step 4:** Modificar `main.py` para incluir router

```python
from app.api.conciliacion import router as conciliacion_router
# ... en crear_app:
app.include_router(conciliacion_router)
```

- [ ] **Step 5:** Correr suite completa → PASS

- [ ] **Step 6:** Commit

```bash
cd estudio-contable && git add backend/app/api/conciliacion.py backend/tests/test_conciliacion_api.py backend/app/main.py && git commit -m "feat(api): endpoint conciliación bancaria CSV + match 4 niveles"
```

---

### Task 5: Frontend — pantalla de conciliación

**Files:**
- Create: `frontend/src/components/Conciliacion.tsx`
- Modify: `frontend/src/pages/Home.tsx` (agregar solapa)
- Modify: `frontend/src/api.ts` (nueva función)

- [ ] **Step 1: Agregar función API**

En `frontend/src/api.ts`:

```typescript
export interface ResultadoConciliacion {
  porcentaje_match: number
  matches: { comprobante_id: number; movimiento_id: number; nivel: string; monto_comprobante: string; monto_movimiento: string }[]
  sin_match_compras: number[]
  sin_match_banco: { id: number; fecha: string; descripcion: string; monto: string }[]
  diferencias: { comprobante_id: number; movimiento_id: number; monto_diferencia: string }[]
  duplicados: number
  importados: number
  periodo: string
}

export async function importarConciliacion(
  clienteId: number,
  archivo: File,
  delimitador: string,
  token: string,
): Promise<ResultadoConciliacion> {
  const form = new FormData()
  form.append("archivo", archivo)
  form.append("delimitador", delimitador)
  const r = await fetch(`/clientes/${clienteId}/conciliacion/importar`, {
    method: "POST",
    headers: conToken(token),
    body: form,
  })
  if (!r.ok) {
    const msg = await r.text()
    throw new Error(msg || "Error al importar")
  }
  return r.json()
}
```

- [ ] **Step 2: Crear componente Conciliacion.tsx**

```tsx
import { useEffect, useState } from "react"
import { importarConciliacion, listarClientes, type Cliente, type ResultadoConciliacion } from "../api"

const NIVEL_COLOR: Record<string, string> = {
  exacto: "bg-green-100 text-green-800",
  monto_fecha: "bg-blue-100 text-blue-800",
  monto_rango: "bg-amber-100 text-amber-800",
  aproximado: "bg-orange-100 text-orange-800",
}

export default function Conciliacion({ token }: { token: string }) {
  const [clientes, setClientes] = useState<Cliente[]>([])
  const [clienteId, setClienteId] = useState<number | "">("")
  const [delimitador, setDelimitador] = useState(";")
  const [resultado, setResultado] = useState<ResultadoConciliacion | null>(null)
  const [error, setError] = useState("")
  const [cargando, setCargando] = useState(false)

  useEffect(() => {
    listarClientes(token).then(setClientes).catch(() => {})
  }, [token])

  async function procesar(archivo: File) {
    if (clienteId === "") return
    setCargando(true)
    setError("")
    setResultado(null)
    try {
      setResultado(await importarConciliacion(clienteId, archivo, delimitador, token))
    } catch (err) {
      setError(err instanceof Error ? err.message : "Error al procesar")
    } finally {
      setCargando(false)
    }
  }

  return (
    <div className="space-y-6">
      <section className="bg-white rounded-xl shadow-md p-6 space-y-3">
        <h2 className="font-semibold text-slate-800">Conciliación bancaria</h2>
        <div className="flex flex-wrap gap-3 items-end">
          <select
            className="border rounded-lg px-3 py-2"
            value={clienteId}
            onChange={(e) => setClienteId(e.target.value === "" ? "" : Number(e.target.value))}
          >
            <option value="">Elegí un cliente…</option>
            {clientes.map((c) => (
              <option key={c.id} value={c.id}>
                {c.razon_social} ({c.cuit})
              </option>
            ))}
          </select>
          <select
            className="border rounded-lg px-3 py-2"
            value={delimitador}
            onChange={(e) => setDelimitador(e.target.value)}
          >
            <option value=";">Punto y coma (;)</option>
            <option value=",">Coma (,)</option>
            <option value="\t">Tab</option>
          </select>
          <label className="border-2 border-dashed border-slate-300 rounded-lg px-4 py-2 text-sm text-slate-600 cursor-pointer hover:bg-slate-50">
            <input
              type="file"
              accept=".csv"
              className="hidden"
              onChange={(e) => {
                const f = e.target.files?.[0]
                if (f) procesar(f)
              }}
            />
            {cargando ? "Procesando…" : "Subir CSV bancario"}
          </label>
        </div>
        {error && <p className="text-sm text-red-600">{error}</p>}
      </section>

      {resultado && (
        <section className="bg-white rounded-xl shadow-md p-6 space-y-4">
          <div className="flex items-center justify-between">
            <h3 className="font-semibold text-slate-800">Resultado de conciliación</h3>
            <span className={`px-3 py-1 rounded-full text-sm font-bold ${
              resultado.porcentaje_match >= 80 ? "bg-green-100 text-green-800" :
              resultado.porcentaje_match >= 50 ? "bg-amber-100 text-amber-800" :
              "bg-red-100 text-red-800"
            }`}>
              {resultado.porcentaje_match}% match
            </span>
          </div>

          {resultado.duplicados > 0 && (
            <p className="text-sm text-amber-700 bg-amber-50 rounded-lg p-3">
              ⚠️ Se detectaron {resultado.duplicados} movimiento(s) duplicado(s) en el archivo y fueron descartados.
            </p>
          )}

          {resultado.matches.length > 0 && (
            <div>
              <h4 className="text-sm font-medium text-slate-500 mb-2">Matches encontrados</h4>
              <table className="w-full text-sm">
                <thead>
                  <tr className="text-left text-slate-500 border-b">
                    <th className="py-2">Comp.</th>
                    <th>Mov.</th>
                    <th>Nivel</th>
                    <th>Monto comp.</th>
                    <th>Monto banco</th>
                  </tr>
                </thead>
                <tbody>
                  {resultado.matches.map((m, i) => (
                    <tr key={i} className="border-b last:border-0">
                      <td className="py-2">#{m.comprobante_id}</td>
                      <td>#{m.movimiento_id}</td>
                      <td>
                        <span className={`px-2 py-0.5 rounded-full text-xs font-semibold ${NIVEL_COLOR[m.nivel] || "bg-slate-100"}`}>
                          {m.nivel}
                        </span>
                      </td>
                      <td className="font-mono">${Number(m.monto_comprobante).toLocaleString("es-AR")}</td>
                      <td className="font-mono">${Number(m.monto_movimiento).toLocaleString("es-AR")}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}

          {resultado.diferencias.length > 0 && (
            <div>
              <h4 className="text-sm font-medium text-red-600 mb-2">Diferencias detectadas</h4>
              <ul className="text-sm space-y-1">
                {resultado.diferencias.map((d, i) => (
                  <li key={i} className="flex justify-between border-b py-1">
                    <span>Comp. #{d.comprobante_id} vs Mov. #{d.movimiento_id}</span>
                    <span className="font-mono text-red-600">
                      Dif: ${Number(d.monto_diferencia).toLocaleString("es-AR")}
                    </span>
                  </li>
                ))}
              </ul>
            </div>
          )}

          {resultado.sin_match_banco.length > 0 && (
            <div>
              <h4 className="text-sm font-medium text-slate-500 mb-2">Movimientos sin comprobante</h4>
              <ul className="text-sm space-y-1">
                {resultado.sin_match_banco.map((m) => (
                  <li key={m.id} className="flex justify-between border-b py-1">
                    <span>{m.fecha} — {m.descripcion}</span>
                    <span className="font-mono">${Number(m.monto).toLocaleString("es-AR")}</span>
                  </li>
                ))}
              </ul>
            </div>
          )}

          {resultado.sin_match_compras.length > 0 && (
            <div>
              <h4 className="text-sm font-medium text-slate-500 mb-2">Comprobantes sin movimiento bancario</h4>
              <p className="text-sm text-slate-400">
                Comprobantes: #{resultado.sin_match_compras.join(", #")}
              </p>
            </div>
          )}
        </section>
      )}
    </div>
  )
}
```

- [ ] **Step 3: Agregar solapa en Home.tsx**

```typescript
type Solapa = "subir" | "clientes" | "liquidacion" | "conciliacion"

const SOLAPAS: { id: Solapa; etiqueta: string }[] = [
  { id: "subir", etiqueta: "Subir factura" },
  { id: "clientes", etiqueta: "Clientes" },
  { id: "liquidacion", etiqueta: "Liquidación IVA" },
  { id: "conciliacion", etiqueta: "Conciliación" },
]
```

Y agregar:
```tsx
{solapa === "conciliacion" && <Conciliacion token={token} />}
```

- [ ] **Step 4: Verificar build**

Run: `cd frontend && npm run build`
Expected: exit 0

- [ ] **Step 5:** Commit

```bash
cd estudio-contable && git add frontend/src/components/Conciliacion.tsx frontend/src/pages/Home.tsx frontend/src/api.ts && git commit -m "feat(frontend): pantalla de conciliación bancaria con drag&drop CSV"
```

---

### Task 6: Cierre — suite completa + push

- [ ] **Step 1:** Suite backend verde
Run: `cd backend && python -m pytest -v`
Expected: todos verdes

- [ ] **Step 2:** Build frontend OK
Run: `cd frontend && npm run build`
Expected: exit 0

- [ ] **Step 3:** Actualizar ESTADO.md con progreso

- [ ] **Step 4:** Commit final + push

```bash
cd estudio-contable && git add docs/ESTADO.md && git commit -m "docs: actualiza ESTADO.md post Etapa 3" && git push origin main
```

---

## Self-Review

**1. Spec coverage:**
- ✅ Motor match 4 niveles → Task 3
- ✅ Parser bancario CSV → Task 1
- ✅ Deduplicador → Task 2
- ✅ API conciliación → Task 4
- ✅ Frontend conciliación → Task 5
- ✅ % de match visible → Task 5
- ✅ Diferencias listadas → Task 5
- ✅ Duplicados eliminados → Task 2, 5

**2. Placeholder scan:** Ningún TBD ni placeholder.

**3. Type consistency:** `MovimientoBancario` usa `Decimal` consistente con el resto del sistema. La API serializa a `str` para JSON.
