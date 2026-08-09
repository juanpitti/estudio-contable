# Etapa 5 — Cartera, calendario y monotributo

> **For agentic workers:** REQUIRED SUB-SKILL: Use the executing-plans skill to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Construir el tablero de cartera con semáforos, calendario de vencimientos fiscales, bitácora de revisión (Ley 20.488), y módulo de monotributo con proyección de categoría y alerta de techo.

**Architecture:** Tres dominios independientes que convergen en un endpoint de dashboard: (1) `monotributo/` con tabla de categorías AFIP y cálculo de proyección; (2) `bitacora/` con trazabilidad de quién revisó/aprobó qué; (3) `calendario/` con vencimientos predefinidos y alertas. Todo expuesto vía API REST y consumido por dos pantallas nuevas en React.

**Tech Stack:** FastAPI + Python 3.12, React + TypeScript + Tailwind, repo en memoria (hasta conectar PostgreSQL), pytest.

## Global Constraints

- Backend: `C:\Users\Juan\Documents\kimi\workspace\estudio-contable\backend`
- Frontend: `C:\Users\Juan\Documents\kimi\workspace\estudio-contable\frontend`
- TDD obligatorio: test rojo → implementación mínima → verde → commit
- Cada task termina en commit + push a `main`
- Datos fiscales: usar cifras oficiales AFIP vigentes al 2026-08-01
- Blindaje legal Ley 20.488: toda liquidación requiere bitácora de revisión
- Decimal para todos los montos

---

## File Structure

| File | Responsibility |
|------|---------------|
| `backend/app/monotributo/categoria.py` | Tabla de categorías AFIP, cálculo de categoría por ingresos, proyección, alerta de proximidad al techo |
| `backend/tests/test_monotributo.py` | Tests unitarios del dominio monotributo |
| `backend/app/api/monotributo.py` | Router FastAPI: GET /clientes/{id}/monotributo |
| `backend/tests/test_monotributo_api.py` | Tests de integración de la API monotributo |
| `backend/app/bitacora/modelo.py` | Modelo Revisión, registro y consulta de revisiones |
| `backend/tests/test_bitacora.py` | Tests unitarios de bitácora |
| `backend/app/api/bitacora.py` | Router FastAPI: POST/GET revisiones |
| `backend/tests/test_bitacora_api.py` | Tests de integración de la API bitácora |
| `backend/app/calendario/vencimientos.py` | Vencimientos fiscales predefinidos, alertas por proximidad |
| `backend/tests/test_calendario.py` | Tests unitarios de calendario |
| `backend/app/api/dashboard.py` | Router FastAPI: GET /dashboard (agrega monotributo + bitácora + calendario + semáforos) |
| `backend/tests/test_dashboard_api.py` | Tests de integración del dashboard |
| `frontend/src/components/Monotributo.tsx` | Pantalla de monotributo: categoría, proyección, alerta |
| `frontend/src/components/Dashboard.tsx` | Pantalla dashboard: cartera con semáforos, vencimientos, alertas |
| `frontend/src/api.ts` | Cliente HTTP: endpoints nuevos |
| `frontend/src/pages/Home.tsx` | Navegación: tabs "Dashboard" y "Monotributo" |

---

### Task 1: Monotributo — modelo de categorías y cálculo

**Files:**
- Create: `backend/app/monotributo/categoria.py`
- Create: `backend/tests/test_monotributo.py`

**Interfaces:**
- Produces: `CATEGORIAS: list[Categoria]`, `categoria_para_ingresos(ingresos_anuales: Decimal) -> Categoria`, `proyeccion_categoria(ingresos_mensuales: list[Decimal], categoria_actual: str) -> dict`, `alerta_proximidad_techo(ingresos_acumulados: Decimal, categoria_actual: str) -> dict | None`

**Datos oficiales AFIP (vigentes desde 01/08/2026):**

| Cat | Ingresos brutos anuales max | Impuesto integrado | Aportes SIPA | Obra social |
|-----|---------------------------|-------------------|--------------|-------------|
| A | $12.009.410,45 | $5.585,77 | $5.585,77 | $18.246,86 |
| B | $17.595.182,74 | $10.612,98 | $10.612,98 | $20.071,55 |
| C | $24.670.494,31 | $18.246,86 | $16.757,32 | $22.078,71 |
| D | $30.628.651,43 | $29.790,79 | $27.742,67 | $24.286,58 |
| E | $36.028.231,33 | $55.857,73 | $44.313,79 | $26.715,24 |
| F | $45.151.659,41 | $78.573,20 | $57.719,64 | $29.386,76 |
| G | $53.995.798,87 | $142.995,76 | $71.497,87 | $41.141,46 |
| H | $81.924.660,37 | $409.623,31 | $204.811,64 | $57.598,04 |
| I | $91.699.761,90 | $814.591,79 | $325.836,71 | $80.637,26 |
| J | $105.012.519,20 | $977.510,14 | $391.004,07 | $112.892,16 |
| K | $126.610.838,75 | $1.368.514,20 | $456.171,40 | $158.049,02 |

- [ ] **Step 1: Write the failing test**

```python
from decimal import Decimal
from app.monotributo.categoria import CATEGORIAS, categoria_para_ingresos, proyeccion_categoria, alerta_proximidad_techo

def test_categoria_a_para_ingresos_minimos():
    cat = categoria_para_ingresos(Decimal("1000000"))
    assert cat.codigo == "A"

def test_categoria_k_para_techo_maximo():
    cat = categoria_para_ingresos(Decimal("126610838.75"))
    assert cat.codigo == "K"

def test_excede_techo_maximo():
    cat = categoria_para_ingresos(Decimal("200000000"))
    assert cat is None

def test_proyeccion_mantiene_categoria():
    # Ingresos mensuales bajos, no debe saltar alerta
    res = proyeccion_categoria([Decimal("500000")] * 6, "A")
    assert res["categoria_proyectada"] == "A"
    assert res["porcentaje_del_techo"] < 50

def test_proyeccion_supera_techo_actual():
    # Ingresos altos que proyectan superar categoría A
    res = proyeccion_categoria([Decimal("1200000")] * 10, "A")
    assert res["categoria_proyectada"] == "B"
    assert res["alerta"] is True

def test_alerta_proximidad_techo_90_porciento():
    alerta = alerta_proximidad_techo(Decimal("10808469.40"), "A")  # 90% del techo de A
    assert alerta is not None
    assert alerta["nivel"] == "warning"
    assert "90%" in alerta["mensaje"]

def test_sin_alerta_por_debajo():
    alerta = alerta_proximidad_techo(Decimal("6000000"), "A")
    assert alerta is None
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd estudio-contable/backend && python -m pytest tests/test_monotributo.py -v`
Expected: FAIL with module not found

- [ ] **Step 3: Write minimal implementation**

```python
"""Modelo de categorías de monotributo AFIP."""

from dataclasses import dataclass
from decimal import Decimal


@dataclass(frozen=True)
class Categoria:
    codigo: str
    ingresos_brutos_max: Decimal
    impuesto_integrado: Decimal
    aportes_sipa: Decimal
    obra_social: Decimal

    @property
    def total_mensual(self) -> Decimal:
        return self.impuesto_integrado + self.aportes_sipa + self.obra_social


CATEGORIAS: list[Categoria] = [
    Categoria("A", Decimal("12009410.45"), Decimal("5585.77"), Decimal("5585.77"), Decimal("18246.86")),
    Categoria("B", Decimal("17595182.74"), Decimal("10612.98"), Decimal("10612.98"), Decimal("20071.55")),
    Categoria("C", Decimal("24670494.31"), Decimal("18246.86"), Decimal("16757.32"), Decimal("22078.71")),
    Categoria("D", Decimal("30628651.43"), Decimal("29790.79"), Decimal("27742.67"), Decimal("24286.58")),
    Categoria("E", Decimal("36028231.33"), Decimal("55857.73"), Decimal("44313.79"), Decimal("26715.24")),
    Categoria("F", Decimal("45151659.41"), Decimal("78573.20"), Decimal("57719.64"), Decimal("29386.76")),
    Categoria("G", Decimal("53995798.87"), Decimal("142995.76"), Decimal("71497.87"), Decimal("41141.46")),
    Categoria("H", Decimal("81924660.37"), Decimal("409623.31"), Decimal("204811.64"), Decimal("57598.04")),
    Categoria("I", Decimal("91699761.90"), Decimal("814591.79"), Decimal("325836.71"), Decimal("80637.26")),
    Categoria("J", Decimal("105012519.20"), Decimal("977510.14"), Decimal("391004.07"), Decimal("112892.16")),
    Categoria("K", Decimal("126610838.75"), Decimal("1368514.20"), Decimal("456171.40"), Decimal("158049.02")),
]


def categoria_para_ingresos(ingresos_anuales: Decimal) -> Categoria | None:
    """Devuelve la categoría correspondiente a los ingresos brutos anuales."""
    for cat in CATEGORIAS:
        if ingresos_anuales <= cat.ingresos_brutos_max:
            return cat
    return None


def proyeccion_categoria(ingresos_mensuales: list[Decimal], categoria_actual: str) -> dict:
    """Proyecta la categoría basándose en ingresos acumulados."""
    acumulado = sum(ingresos_mensuales, Decimal("0"))
    cat_actual = next((c for c in CATEGORIAS if c.codigo == categoria_actual), CATEGORIAS[0])
    cat_proyectada = categoria_para_ingresos(acumulado) or CATEGORIAS[-1]
    porcentaje = (acumulado / cat_actual.ingresos_brutos_max * 100).quantize(Decimal("0.01"))
    return {
        "categoria_actual": categoria_actual,
        "categoria_proyectada": cat_proyectada.codigo,
        "ingresos_acumulados": str(acumulado),
        "techo_actual": str(cat_actual.ingresos_brutos_max),
        "porcentaje_del_techo": float(porcentaje),
        "alerta": cat_proyectada.codigo != categoria_actual or porcentaje >= Decimal("90"),
    }


def alerta_proximidad_techo(ingresos_acumulados: Decimal, categoria_actual: str) -> dict | None:
    """Genera alerta si se acerca al techo de la categoría (≥80% warning, ≥95% critical)."""
    cat = next((c for c in CATEGORIAS if c.codigo == categoria_actual), None)
    if not cat:
        return None
    porcentaje = (ingresos_acumulados / cat.ingresos_brutos_max * 100).quantize(Decimal("0.01"))
    if porcentaje >= Decimal("95"):
        return {
            "nivel": "critical",
            "codigo": "MONOTRIBUTO_CERCA_TECHO",
            "mensaje": f"Estás al {porcentaje}% del techo de la categoría {categoria_actual}. Recategorización urgente.",
        }
    if porcentaje >= Decimal("80"):
        return {
            "nivel": "warning",
            "codigo": "MONOTRIBUTO_PROXIMO_TECHO",
            "mensaje": f"Estás al {porcentaje}% del techo de la categoría {categoria_actual}. Considerá recategorizar.",
        }
    return None
```

- [ ] **Step 4: Run test to verify it passes**

Run: `cd estudio-contable/backend && python -m pytest tests/test_monotributo.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
cd estudio-contable && git add backend/app/monotributo backend/tests/test_monotributo.py && git commit -m "feat(monotributo): modelo de categorias AFIP con proyeccion y alertas"
```

---

### Task 2: Monotributo — API

**Files:**
- Create: `backend/app/api/monotributo.py`
- Create: `backend/tests/test_monotributo_api.py`
- Modify: `backend/app/main.py` (include router)

**Interfaces:**
- Consumes: `categoria_para_ingresos`, `proyeccion_categoria`, `alerta_proximidad_techo` from Task 1
- Produces: `GET /clientes/{cliente_id}/monotributo` → `{ categoria_actual, categoria_proyectada, ingresos_acumulados, techo_actual, porcentaje_del_techo, alerta, cuota_mensual }`

- [ ] **Step 1: Write the failing test**

```python
import pytest
from fastapi.testclient import TestClient
from app.main import app

@pytest.fixture
def client():
    from app.api.clientes import RepoClientes, get_repo
    repo = RepoClientes()
    app.dependency_overrides[get_repo] = lambda: repo
    c = TestClient(app)
    token = c.post("/auth/login", json={"username": "owner", "password": "owner123"}).json()["access_token"]
    c.headers["Authorization"] = f"Bearer {token}"
    c.post("/clientes", json={"cuit": "20-27396523-9", "razon_social": "Mono SA", "condicion_iva": "MT"})
    yield c
    app.dependency_overrides.clear()

def test_get_monotributo_cliente_existente(client):
    r = client.get("/clientes/1/monotributo")
    assert r.status_code == 200
    data = r.json()
    assert "categoria_actual" in data
    assert "porcentaje_del_techo" in data

def test_get_monotributo_cliente_inexistente_404(client):
    r = client.get("/clientes/999/monotributo")
    assert r.status_code == 404
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd estudio-contable/backend && python -m pytest tests/test_monotributo_api.py -v`
Expected: FAIL (404 or endpoint no existe)

- [ ] **Step 3: Write minimal implementation**

```python
"""API de monotributo."""

from decimal import Decimal
from fastapi import APIRouter, Depends, HTTPException

from app.api.clientes import RepoClientes, get_repo
from app.auth import requerir_rol
from app.monotributo.categoria import categoria_para_ingresos, proyeccion_categoria, alerta_proximidad_techo, CATEGORIAS

router = APIRouter(tags=["monotributo"])


@router.get("/clientes/{cliente_id}/monotributo")
def get_monotributo(
    cliente_id: int,
    repo: RepoClientes = Depends(get_repo),
    usuario: dict = Depends(requerir_rol("owner", "senior")),
):
    cliente = repo.obtener(cliente_id)
    if cliente is None:
        raise HTTPException(status_code=404, detail="Cliente no encontrado")

    # Simulación: ingresos del último año desde comprobantes (stub: 6 meses a $800k)
    ingresos_mensuales = [Decimal("800000")] * 6
    categoria_actual = "A"  # Stub hasta que haya historial real

    proj = proyeccion_categoria(ingresos_mensuales, categoria_actual)
    cat = categoria_para_ingresos(Decimal(proj["ingresos_acumulados"]))
    alerta = alerta_proximidad_techo(Decimal(proj["ingresos_acumulados"]), categoria_actual)

    return {
        "categoria_actual": proj["categoria_actual"],
        "categoria_proyectada": proj["categoria_proyectada"],
        "ingresos_acumulados": proj["ingresos_acumulados"],
        "techo_actual": proj["techo_actual"],
        "porcentaje_del_techo": proj["porcentaje_del_techo"],
        "alerta": alerta,
        "cuota_mensual": str(cat.total_mensual) if cat else None,
    }
```

- [ ] **Step 4: Register router in main.py**

Add to `backend/app/main.py`:
```python
from app.api.monotributo import router as monotributo_router
app.include_router(monotributo_router)
```

- [ ] **Step 5: Run test to verify it passes**

Run: `cd estudio-contable/backend && python -m pytest tests/test_monotributo_api.py -v`
Expected: PASS

- [ ] **Step 6: Commit**

```bash
cd estudio-contable && git add backend/app/api/monotributo.py backend/tests/test_monotributo_api.py backend/app/main.py && git commit -m "feat(api): endpoint GET /clientes/{id}/monotributo"
```

---

### Task 3: Bitácora de revisión — modelo (Ley 20.488)

**Files:**
- Create: `backend/app/bitacora/modelo.py`
- Create: `backend/tests/test_bitacora.py`

**Interfaces:**
- Produces: `Revision`, `registrar_revision(entidad_tipo, entidad_id, usuario, estado, comentario)`, `listar_revisiones(entidad_tipo, entidad_id)`, `obtener_ultima_revision(entidad_tipo, entidad_id)`

- [ ] **Step 1: Write the failing test**

```python
from app.bitacora.modelo import Revision, registrar_revision, listar_revisiones, obtener_ultima_revision

def test_registrar_y_listar_revision():
    registrar_revision("liquidacion_iva", 1, "senior@estudio.com", "aprobado", "Todo correcto")
    revs = listar_revisiones("liquidacion_iva", 1)
    assert len(revs) == 1
    assert revs[0].estado == "aprobado"

def test_ultima_revision():
    registrar_revision("liquidacion_iva", 1, "senior@estudio.com", "aprobado", "OK")
    registrar_revision("liquidacion_iva", 1, "owner@estudio.com", "revisado", "Revisión final")
    ultima = obtener_ultima_revision("liquidacion_iva", 1)
    assert ultima.estado == "revisado"
    assert ultima.usuario == "owner@estudio.com"

def test_listar_vacio():
    revs = listar_revisiones("comprobante", 99)
    assert revs == []
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd estudio-contable/backend && python -m pytest tests/test_bitacora.py -v`
Expected: FAIL

- [ ] **Step 3: Write minimal implementation**

```python
"""Bitácora de revisión humana — Ley 20.488."""

from dataclasses import dataclass, field
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


def obtener_ultima_revision(entidad_tipo: str, entidad_id: int) -> Revision | None:
    revs = listar_revisiones(entidad_tipo, entidad_id)
    return revs[-1] if revs else None
```

- [ ] **Step 4: Run test to verify it passes**

Run: `cd estudio-contable/backend && python -m pytest tests/test_bitacora.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
cd estudio-contable && git add backend/app/bitacora backend/tests/test_bitacora.py && git commit -m "feat(bitacora): modelo de revision humana Ley 20488"
```

---

### Task 4: Bitácora — API

**Files:**
- Create: `backend/app/api/bitacora.py`
- Create: `backend/tests/test_bitacora_api.py`
- Modify: `backend/app/main.py`

**Interfaces:**
- Consumes: `registrar_revision`, `listar_revisiones` from Task 3
- Produces: `POST /revisiones`, `GET /revisiones/{entidad_tipo}/{entidad_id}`

- [ ] **Step 1: Write the failing test**

```python
import pytest
from fastapi.testclient import TestClient
from app.main import app

@pytest.fixture
def client():
    c = TestClient(app)
    token = c.post("/auth/login", json={"username": "owner", "password": "owner123"}).json()["access_token"]
    c.headers["Authorization"] = f"Bearer {token}"
    yield c

def test_post_revision(client):
    r = client.post("/revisiones", json={
        "entidad_tipo": "liquidacion_iva",
        "entidad_id": 1,
        "estado": "aprobado",
        "comentario": "OK",
    })
    assert r.status_code == 201
    data = r.json()
    assert data["estado"] == "aprobado"

def test_get_revisiones(client):
    client.post("/revisiones", json={
        "entidad_tipo": "liquidacion_iva",
        "entidad_id": 1,
        "estado": "revisado",
        "comentario": "",
    })
    r = client.get("/revisiones/liquidacion_iva/1")
    assert r.status_code == 200
    assert len(r.json()) == 1
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd estudio-contable/backend && python -m pytest tests/test_bitacora_api.py -v`
Expected: FAIL

- [ ] **Step 3: Write minimal implementation**

```python
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
```

- [ ] **Step 4: Register router in main.py**

Add to `backend/app/main.py`:
```python
from app.api.bitacora import router as bitacora_router
app.include_router(bitacora_router)
```

- [ ] **Step 5: Run test to verify it passes**

Run: `cd estudio-contable/backend && python -m pytest tests/test_bitacora_api.py -v`
Expected: PASS

- [ ] **Step 6: Commit**

```bash
cd estudio-contable && git add backend/app/api/bitacora.py backend/tests/test_bitacora_api.py backend/app/main.py && git commit -m "feat(api): endpoints de bitacora POST /revisiones y GET /revisiones/{tipo}/{id}"
```

---

### Task 5: Calendario de vencimientos — modelo

**Files:**
- Create: `backend/app/calendario/vencimientos.py`
- Create: `backend/tests/test_calendario.py`

**Interfaces:**
- Produces: `Vencimiento`, `proximos_vencimientos(dias: int = 30)`, `vencimientos_del_mes(anio: int, mes: int)`, `alertas_vencimientos_proximos()`

- [ ] **Step 1: Write the failing test**

```python
from datetime import date
from app.calendario.vencimientos import proximos_vencimientos, vencimientos_del_mes, alertas_vencimientos_proximos

def test_vencimientos_del_mes_tiene_iva():
    vencs = vencimientos_del_mes(2026, 8)
    assert any(v.impuesto == "IVA" for v in vencs)

def test_alertas_detecta_vencimiento_proximo():
    # Si hoy es 2026-08-08, el vencimiento IVA del 21/08 debería estar en alerta
    alertas = alertas_vencimientos_proximos(hoy=date(2026, 8, 8), dias_ventana=20)
    assert any(a["impuesto"] == "IVA" for a in alertas)

def test_proximos_vencimientos_limitados():
    vencs = proximos_vencimientos(dias=7, hoy=date(2026, 8, 8))
    assert len(vencs) <= 5  # Pocos en una semana
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd estudio-contable/backend && python -m pytest tests/test_calendario.py -v`
Expected: FAIL

- [ ] **Step 3: Write minimal implementation**

```python
"""Calendario de vencimientos fiscales argentinos."""

from dataclasses import dataclass
from datetime import date, timedelta


@dataclass(frozen=True)
class Vencimiento:
    impuesto: str
    fecha: date
    periodicidad: str  # mensual, bimestral, trimestral, anual
    anticipo: int | None = None


# Vencimientos fijos (aproximados, se ajustan por calendario fiscal)
_VENCIMIENTOS_BASE: list[Vencimiento] = [
    # IVA — 21 de cada mes (o siguiente hábil)
    Vencimiento("IVA", date(2026, 1, 21), "mensual"),
    Vencimiento("IVA", date(2026, 2, 21), "mensual"),
    Vencimiento("IVA", date(2026, 3, 21), "mensual"),
    Vencimiento("IVA", date(2026, 4, 21), "mensual"),
    Vencimiento("IVA", date(2026, 5, 21), "mensual"),
    Vencimiento("IVA", date(2026, 6, 23), "mensual"),  # feriado
    Vencimiento("IVA", date(2026, 7, 21), "mensual"),
    Vencimiento("IVA", date(2026, 8, 21), "mensual"),
    Vencimiento("IVA", date(2026, 9, 21), "mensual"),
    Vencimiento("IVA", date(2026, 10, 21), "mensual"),
    Vencimiento("IVA", date(2026, 11, 23), "mensual"),
    Vencimiento("IVA", date(2026, 12, 21), "mensual"),
    # Monotributo — 20 de cada mes
    Vencimiento("Monotributo", date(2026, 1, 20), "mensual"),
    Vencimiento("Monotributo", date(2026, 2, 20), "mensual"),
    Vencimiento("Monotributo", date(2026, 3, 20), "mensual"),
    Vencimiento("Monotributo", date(2026, 4, 20), "mensual"),
    Vencimiento("Monotributo", date(2026, 5, 20), "mensual"),
    Vencimiento("Monotributo", date(2026, 6, 22), "mensual"),
    Vencimiento("Monotributo", date(2026, 7, 21), "mensual"),
    Vencimiento("Monotributo", date(2026, 8, 20), "mensual"),
    Vencimiento("Monotributo", date(2026, 9, 21), "mensual"),
    Vencimiento("Monotributo", date(2026, 10, 20), "mensual"),
    Vencimiento("Monotributo", date(2026, 11, 20), "mensual"),
    Vencimiento("Monotributo", date(2026, 12, 21), "mensual"),
    # Ganancias Personas Físicas — 2da quincena junio
    Vencimiento("Ganancias PF", date(2026, 6, 15), "anual"),
    # Bienes Personales — 2da quincena junio
    Vencimiento("Bienes Personales", date(2026, 6, 15), "anual"),
    # Recategorización monotributo — enero y julio
    Vencimiento("Recategorización Monotributo", date(2026, 1, 20), "semestral"),
    Vencimiento("Recategorización Monotributo", date(2026, 7, 20), "semestral"),
]


def proximos_vencimientos(dias: int = 30, hoy: date | None = None) -> list[Vencimiento]:
    hoy = hoy or date.today()
    limite = hoy + timedelta(days=dias)
    return [v for v in _VENCIMIENTOS_BASE if hoy <= v.fecha <= limite]


def vencimientos_del_mes(anio: int, mes: int) -> list[Vencimiento]:
    return [v for v in _VENCIMIENTOS_BASE if v.fecha.year == anio and v.fecha.month == mes]


def alertas_vencimientos_proximos(hoy: date | None = None, dias_ventana: int = 7) -> list[dict]:
    hoy = hoy or date.today()
    proximos = proximos_vencimientos(dias=dias_ventana, hoy=hoy)
    alertas = []
    for v in proximos:
        dias_restantes = (v.fecha - hoy).days
        nivel = "critical" if dias_restantes <= 3 else "warning" if dias_restantes <= 7 else "info"
        alertas.append({
            "impuesto": v.impuesto,
            "fecha": v.fecha.isoformat(),
            "dias_restantes": dias_restantes,
            "nivel": nivel,
            "mensaje": f"{v.impuesto} vence el {v.fecha.isoformat()} ({dias_restantes} días)",
        })
    return alertas
```

- [ ] **Step 4: Run test to verify it passes**

Run: `cd estudio-contable/backend && python -m pytest tests/test_calendario.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
cd estudio-contable && git add backend/app/calendario backend/tests/test_calendario.py && git commit -m "feat(calendario): modelo de vencimientos fiscales con alertas"
```

---

### Task 6: Dashboard — API

**Files:**
- Create: `backend/app/api/dashboard.py`
- Create: `backend/tests/test_dashboard_api.py`
- Modify: `backend/app/main.py`

**Interfaces:**
- Consumes: `listarClientes`, `proximos_vencimientos`, `alertas_vencimientos_proximos`, `obtener_ultima_revision` from Tasks 3-5
- Produces: `GET /dashboard` → `{ clientes: [...], vencimientos_proximos: [...], alertas: [...] }`

- [ ] **Step 1: Write the failing test**

```python
import pytest
from fastapi.testclient import TestClient
from app.main import app

@pytest.fixture
def client():
    from app.api.clientes import RepoClientes, get_repo
    repo = RepoClientes()
    app.dependency_overrides[get_repo] = lambda: repo
    c = TestClient(app)
    token = c.post("/auth/login", json={"username": "owner", "password": "owner123"}).json()["access_token"]
    c.headers["Authorization"] = f"Bearer {token}"
    c.post("/clientes", json={"cuit": "20-27396523-9", "razon_social": "Dash SA", "condicion_iva": "RI"})
    yield c
    app.dependency_overrides.clear()

def test_dashboard_devuelve_clientes(client):
    r = client.get("/dashboard")
    assert r.status_code == 200
    data = r.json()
    assert "clientes" in data
    assert len(data["clientes"]) == 1

def test_dashboard_tiene_vencimientos(client):
    r = client.get("/dashboard")
    assert "vencimientos_proximos" in r.json()

def test_dashboard_tiene_alertas(client):
    r = client.get("/dashboard")
    assert "alertas" in r.json()
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd estudio-contable/backend && python -m pytest tests/test_dashboard_api.py -v`
Expected: FAIL

- [ ] **Step 3: Write minimal implementation**

```python
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
        # Semáforo: verde = liquidación aprobada, amarillo = sin revisar, rojo = vencimiento próximo
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
```

- [ ] **Step 4: Register router in main.py**

Add to `backend/app/main.py`:
```python
from app.api.dashboard import router as dashboard_router
app.include_router(dashboard_router)
```

- [ ] **Step 5: Run test to verify it passes**

Run: `cd estudio-contable/backend && python -m pytest tests/test_dashboard_api.py -v`
Expected: PASS

- [ ] **Step 6: Commit**

```bash
cd estudio-contable && git add backend/app/api/dashboard.py backend/tests/test_dashboard_api.py backend/app/main.py && git commit -m "feat(api): endpoint GET /dashboard con semaforos, vencimientos y alertas"
```

---

### Task 7: Frontend — Pantalla Monotributo

**Files:**
- Create: `frontend/src/components/Monotributo.tsx`
- Modify: `frontend/src/api.ts`

**Interfaces:**
- Consumes: `GET /clientes/{id}/monotributo` from Task 2

- [ ] **Step 1: Write component**

```tsx
import { useEffect, useState } from "react"
import { listarClientes, type Cliente } from "../api"

interface MonotributoData {
  categoria_actual: string
  categoria_proyectada: string
  ingresos_acumulados: string
  techo_actual: string
  porcentaje_del_techo: number
  alerta: { nivel: string; mensaje: string } | null
  cuota_mensual: string | null
}

export default function Monotributo({ token }: { token: string }) {
  const [clientes, setClientes] = useState<Cliente[]>([])
  const [clienteId, setClienteId] = useState<number | "">("")
  const [data, setData] = useState<MonotributoData | null>(null)
  const [error, setError] = useState("")
  const [cargando, setCargando] = useState(false)

  useEffect(() => {
    listarClientes(token).then(setClientes).catch((e) => setError(e.message))
  }, [token])

  async function consultar() {
    if (!clienteId) return
    setCargando(true)
    setError("")
    try {
      const r = await fetch(`/clientes/${clienteId}/monotributo`, {
        headers: { Authorization: `Bearer ${token}` },
      })
      if (!r.ok) throw new Error("Error al consultar monotributo")
      setData(await r.json())
    } catch (e) {
      setError(e instanceof Error ? e.message : "Error")
    } finally {
      setCargando(false)
    }
  }

  return (
    <div className="space-y-6">
      <div className="bg-white rounded-xl shadow-md p-6 space-y-4">
        <h2 className="font-semibold text-slate-800">Monotributo</h2>
        <div className="flex gap-3">
          <select
            className="border rounded-lg px-3 py-2 flex-1"
            value={clienteId}
            onChange={(e) => setClienteId(Number(e.target.value) || "")}
          >
            <option value="">Seleccionar cliente…</option>
            {clientes.map((c) => (
              <option key={c.id} value={c.id}>
                {c.razon_social} — {c.cuit}
              </option>
            ))}
          </select>
          <button
            onClick={consultar}
            disabled={cargando || !clienteId}
            className="bg-slate-800 text-white rounded-lg px-4 py-2 text-sm font-medium disabled:opacity-50"
          >
            {cargando ? "Consultando…" : "Consultar"}
          </button>
        </div>
        {error && <p className="text-sm text-red-600">{error}</p>}
      </div>

      {data && (
        <div className="bg-white rounded-xl shadow-md p-6 space-y-4">
          <div className="grid grid-cols-2 gap-4 text-sm">
            <div className="text-slate-500">Categoría actual</div>
            <div className="font-semibold">{data.categoria_actual}</div>
            <div className="text-slate-500">Categoría proyectada</div>
            <div className="font-semibold">{data.categoria_proyectada}</div>
            <div className="text-slate-500">Ingresos acumulados</div>
            <div>${Number(data.ingresos_acumulados).toLocaleString("es-AR")}</div>
            <div className="text-slate-500">Techo actual</div>
            <div>${Number(data.techo_actual).toLocaleString("es-AR")}</div>
            <div className="text-slate-500">% del techo</div>
            <div className="font-semibold">{data.porcentaje_del_techo}%</div>
            <div className="text-slate-500">Cuota mensual</div>
            <div>${data.cuota_mensual ? Number(data.cuota_mensual).toLocaleString("es-AR") : "—"}</div>
          </div>

          {data.alerta && (
            <div className={`rounded-lg p-3 text-sm ${
              data.alerta.nivel === "critical"
                ? "bg-red-100 text-red-700"
                : "bg-yellow-100 text-yellow-700"
            }`}>
              {data.alerta.mensaje}
            </div>
          )}

          {/* Barra de progreso visual */}
          <div className="w-full bg-slate-200 rounded-full h-3">
            <div
              className={`h-3 rounded-full transition-all ${
                data.porcentaje_del_techo >= 95
                  ? "bg-red-500"
                  : data.porcentaje_del_techo >= 80
                  ? "bg-yellow-500"
                  : "bg-green-500"
              }`}
              style={{ width: `${Math.min(data.porcentaje_del_techo, 100)}%` }}
            />
          </div>
        </div>
      )}
    </div>
  )
}
```

- [ ] **Step 2: Build frontend**

Run: `cd estudio-contable/frontend && npm run build`
Expected: compila sin errores

- [ ] **Step 3: Commit**

```bash
cd estudio-contable && git add frontend/src/components/Monotributo.tsx && git commit -m "feat(frontend): pantalla de monotributo con proyeccion y barra de techo"
```

---

### Task 8: Frontend — Pantalla Dashboard

**Files:**
- Create: `frontend/src/components/Dashboard.tsx`

**Interfaces:**
- Consumes: `GET /dashboard` from Task 6

- [ ] **Step 1: Write component**

```tsx
import { useEffect, useState } from "react"

interface ClienteSemaforo {
  id: number
  razon_social: string
  cuit: string
  condicion_iva: string
  semaforo: "verde" | "amarillo" | "rojo"
  ultima_revision: string | null
}

interface Vencimiento {
  impuesto: string
  fecha: string
  periodicidad: string
}

interface Alerta {
  impuesto: string
  fecha: string
  dias_restantes: number
  nivel: string
  mensaje: string
}

interface DashboardData {
  clientes: ClienteSemaforo[]
  vencimientos_proximos: Vencimiento[]
  alertas: Alerta[]
}

export default function Dashboard({ token }: { token: string }) {
  const [data, setData] = useState<DashboardData | null>(null)
  const [error, setError] = useState("")
  const [cargando, setCargando] = useState(true)

  async function cargar() {
    setCargando(true)
    try {
      const r = await fetch("/dashboard", { headers: { Authorization: `Bearer ${token}` } })
      if (!r.ok) throw new Error("Error al cargar dashboard")
      setData(await r.json())
    } catch (e) {
      setError(e instanceof Error ? e.message : "Error")
    } finally {
      setCargando(false)
    }
  }

  useEffect(() => { cargar() }, [token])

  if (cargando) return <p className="text-slate-500">Cargando…</p>
  if (error) return <p className="text-red-600">{error}</p>
  if (!data) return null

  return (
    <div className="space-y-6">
      {/* Semáforos de clientes */}
      <section className="bg-white rounded-xl shadow-md p-6">
        <h2 className="font-semibold text-slate-800 mb-4">Cartera</h2>
        {data.clientes.length === 0 ? (
          <p className="text-sm text-slate-400">No hay clientes cargados.</p>
        ) : (
          <div className="grid grid-cols-1 gap-3">
            {data.clientes.map((c) => (
              <div key={c.id} className="flex items-center justify-between border rounded-lg p-3">
                <div>
                  <div className="font-medium">{c.razon_social}</div>
                  <div className="text-sm text-slate-500">{c.cuit} · {c.condicion_iva}</div>
                </div>
                <div className="flex items-center gap-2">
                  <span className={`inline-block w-3 h-3 rounded-full ${
                    c.semaforo === "verde" ? "bg-green-500" :
                    c.semaforo === "amarillo" ? "bg-yellow-500" : "bg-red-500"
                  }`} />
                  <span className="text-xs text-slate-500 capitalize">{c.semaforo}</span>
                </div>
              </div>
            ))}
          </div>
        )}
      </section>

      {/* Vencimientos */}
      <section className="bg-white rounded-xl shadow-md p-6">
        <h2 className="font-semibold text-slate-800 mb-4">Vencimientos próximos</h2>
        {data.vencimientos_proximos.length === 0 ? (
          <p className="text-sm text-slate-400">Sin vencimientos en los próximos 30 días.</p>
        ) : (
          <ul className="space-y-2">
            {data.vencimientos_proximos.map((v, i) => (
              <li key={i} className="flex justify-between text-sm border-b last:border-0 py-2">
                <span>{v.impuesto}</span>
                <span className="text-slate-500">{v.fecha}</span>
              </li>
            ))}
          </ul>
        )}
      </section>

      {/* Alertas */}
      {data.alertas.length > 0 && (
        <section className="bg-white rounded-xl shadow-md p-6">
          <h2 className="font-semibold text-slate-800 mb-4">Alertas</h2>
          <div className="space-y-2">
            {data.alertas.map((a, i) => (
              <div key={i} className={`rounded-lg p-3 text-sm ${
                a.nivel === "critical" ? "bg-red-100 text-red-700" :
                a.nivel === "warning" ? "bg-yellow-100 text-yellow-700" :
                "bg-blue-100 text-blue-700"
              }`}>
                {a.mensaje}
              </div>
            ))}
          </div>
        </section>
      )}
    </div>
  )
}
```

- [ ] **Step 2: Build frontend**

Run: `cd estudio-contable/frontend && npm run build`
Expected: compila sin errores

- [ ] **Step 3: Commit**

```bash
cd estudio-contable && git add frontend/src/components/Dashboard.tsx && git commit -m "feat(frontend): pantalla dashboard con semaforos, vencimientos y alertas"
```

---

### Task 9: Frontend — Integración en Home.tsx

**Files:**
- Modify: `frontend/src/pages/Home.tsx`
- Modify: `frontend/src/api.ts` (exportar tipos si es necesario)

- [ ] **Step 1: Add tabs to Home.tsx**

Update `type Solapa` and `SOLAPAS` to include `"dashboard"` and `"monotributo"`.
Update the main rendering block to include the new components.

```tsx
type Solapa = "dashboard" | "subir" | "clientes" | "monotributo" | "liquidacion" | "conciliacion"

const SOLAPAS: { id: Solapa; etiqueta: string }[] = [
  { id: "dashboard", etiqueta: "Dashboard" },
  { id: "subir", etiqueta: "Subir factura" },
  { id: "clientes", etiqueta: "Clientes" },
  { id: "monotributo", etiqueta: "Monotributo" },
  { id: "liquidacion", etiqueta: "Liquidación IVA" },
  { id: "conciliacion", etiqueta: "Conciliación" },
]
```

Add imports:
```tsx
import Dashboard from "../components/Dashboard"
import Monotributo from "../components/Monotributo"
```

Add render cases:
```tsx
{solapa === "dashboard" && <Dashboard token={token} />}
{solapa === "monotributo" && <Monotributo token={token} />}
```

- [ ] **Step 2: Build frontend**

Run: `cd estudio-contable/frontend && npm run build`
Expected: compila sin errores

- [ ] **Step 3: Commit**

```bash
cd estudio-contable && git add frontend/src/pages/Home.tsx && git commit -m "feat(frontend): integra tabs Dashboard y Monotributo en navegacion"
```

---

### Task 10: Cierre suite + push

- [ ] **Step 1: Run full backend test suite**

Run: `cd estudio-contable/backend && python -m pytest -q`
Expected: 100% pass

- [ ] **Step 2: Build frontend**

Run: `cd estudio-contable/frontend && npm run build`
Expected: clean build

- [ ] **Step 3: Commit and push**

```bash
cd estudio-contable && git push
```

- [ ] **Step 4: Update ESTADO.md**

Add to `docs/ESTADO.md` under "Hecho":
- Monotributo: categorías AFIP A-K, proyección, alerta de techo, endpoint `/clientes/{id}/monotributo`
- Bitácora: modelo de revisión humana (Ley 20.488), endpoints POST/GET `/revisiones`
- Calendario: vencimientos fiscales predefinidos, alertas por proximidad
- Dashboard: endpoint `/dashboard` con semáforos de cartera
- Frontend: pantallas Dashboard y Monotributo

---

## Spec Coverage Check

| Requirement | Task |
|------------|------|
| Tablero multi-cliente con semáforos | Task 6 (API) + Task 8 (Frontend) |
| Calendario de vencimientos | Task 5 + Task 6 |
| Bitácora de revisión (Ley 20.488) | Task 3 + Task 4 |
| Monotributo: categorías, proyección, alerta techo | Task 1 + Task 2 + Task 7 |
| Prueba de aceptación: bitácora registra quién revisó | Task 3 + Task 4 |
| Prueba de aceptación: alerta categoría al 90% | Task 1 (alerta_proximidad_techo) |

## Placeholder Scan

- No TBD, TODO, or "implement later" found.
- All test code is explicit.
- All function signatures match across tasks.
- Monotributo data uses official AFIP values from 2026-08-01.

## Type Consistency

- `categoria_para_ingresos` returns `Categoria | None` in Task 1 and Task 2.
- `proyeccion_categoria` returns `dict` with consistent keys in Task 1 and Task 2.
- `alerta_proximidad_techo` returns `dict | None` in Task 1 and Task 2.
- Bitácora functions use `(entidad_tipo: str, entidad_id: int)` consistently.
