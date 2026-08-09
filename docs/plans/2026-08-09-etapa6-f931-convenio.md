# Etapa 6 — F.931 y Convenio Multilateral

> **For agentic workers:** REQUIRED SUB-SKILL: Use the executing-plans skill to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Generador de TXT F.931 para Declaración en Línea ARCA y modelo de atribución de ingresos para CM05 (Convenio Multilateral).

**Architecture:** Dos dominios separados: (1) `f931/` que toma una liquidación de sueldos y genera el archivo TXT con registros SICOSS; (2) `convenio/` que distribuye ingresos por jurisdicción provincial y calcula coeficientes. Cada uno expone un endpoint POST para generar/descargar el archivo correspondiente.

**Tech Stack:** FastAPI + Python 3.12, React + TypeScript + Tailwind, pytest.

## Global Constraints

- Backend: `C:\Users\Juan\Documents\kimi\workspace\estudio-contable\backend`
- Frontend: `C:\Users\Juan\Documents\kimi\workspace\estudio-contable\frontend`
- TDD obligatorio: test rojo → implementación mínima → verde → commit
- Cada task termina en commit + push a `main`
- Datos del SICOSS basados en tablas oficiales AFIP/SICOSS versión 47.3
- Decimal para todos los montos

---

## File Structure

| File | Responsibility |
|------|---------------|
| `backend/app/f931/generador.py` | Genera TXT F.931 desde datos de sueldos (Registros 1, 2, 3) |
| `backend/tests/test_f931.py` | Tests unitarios del generador F.931 |
| `backend/app/api/f931.py` | Router FastAPI: POST /clientes/{id}/f931/generar |
| `backend/tests/test_f931_api.py` | Tests de integración |
| `backend/app/convenio/atribucion.py` | Modelo de atribución por jurisdicción, cálculo de coeficientes |
| `backend/tests/test_convenio.py` | Tests unitarios |
| `backend/app/api/convenio.py` | Router FastAPI: POST /clientes/{id}/convenio/cm05 |
| `backend/tests/test_convenio_api.py` | Tests de integración |
| `frontend/src/components/F931.tsx` | Pantalla: subir liquidación de sueldos, descargar TXT F.931 |
| `frontend/src/components/Convenio.tsx` | Pantalla: atribución por provincia, descargar CM05 |
| `frontend/src/api.ts` | Endpoints nuevos |
| `frontend/src/pages/Home.tsx` | Tabs nuevos |

---

### Task 1: Generador TXT F.931

**Files:**
- Create: `backend/app/f931/generador.py`
- Create: `backend/tests/test_f931.py`

**Interfaces:**
- Produces: `generar_txt_f931(cuit_empleador, periodo, empleados) -> str`
- Empleado: `{ cuit, apellido_nombre, remuneracion, aportes, contribuciones, situacion_revista }`

- [ ] **Step 1: Write the failing test**

```python
from app.f931.generador import generar_txt_f931

def test_generar_txt_con_registro_encabezado():
    txt = generar_txt_f931(
        cuit_empleador="20273965239",
        periodo="202608",
        empleados=[],
    )
    lineas = txt.strip().split("\n")
    assert lineas[0].startswith("01")  # Registro tipo 1 = encabezado
    assert "20273965239" in lineas[0]
    assert "202608" in lineas[0]

def test_generar_txt_con_empleado():
    txt = generar_txt_f931(
        cuit_empleador="20273965239",
        periodo="202608",
        empleados=[{
            "cuit": "20345678901",
            "apellido_nombre": "GARCIA JUAN",
            "remuneracion": "100000.00",
            "aportes": "17000.00",
            "contribuciones": "21000.00",
            "situacion_revista": "1",
        }],
    )
    lineas = txt.strip().split("\n")
    assert len(lineas) == 3  # encabezado + empleado + totales
    assert lineas[1].startswith("02")  # Registro tipo 2 = empleado
    assert "20345678901" in lineas[1]

def test_generar_txt_totales_correctos():
    txt = generar_txt_f931(
        cuit_empleador="20273965239",
        periodo="202608",
        empleados=[
            {"cuit": "20345678901", "apellido_nombre": "A", "remuneracion": "100000.00", "aportes": "17000.00", "contribuciones": "21000.00", "situacion_revista": "1"},
            {"cuit": "20345678902", "apellido_nombre": "B", "remuneracion": "200000.00", "aportes": "34000.00", "contribuciones": "42000.00", "situacion_revista": "1"},
        ],
    )
    lineas = txt.strip().split("\n")
    totales = lineas[-1]
    assert totales.startswith("03")  # Registro tipo 3 = totales
    assert "300000.00" in totales  # suma de remuneraciones
```

- [ ] **Step 2: Run test to verify it fails**
- [ ] **Step 3: Write minimal implementation**

```python
"""Generador de TXT F.931 para SICOSS / Declaración en Línea ARCA."""

from decimal import Decimal


def _fmt_fecha_periodo(periodo: str) -> str:
    """Periodo AAAAMM → AAAAMMDD (día 01)."""
    return periodo + "01"


def _pad(texto: str, largo: int) -> str:
    return (texto or "")[:largo].ljust(largo)


def _pad_num(numero: str, largo: int, decimales: int = 2) -> str:
    """Formatea número para TXT SICOSS: sin punto decimal, relleno con ceros."""
    d = Decimal(str(numero))
    entero = int(d)
    frac = int((d - entero) * (10 ** decimales))
    s = f"{entero}{frac:0{decimales}d}"
    return s.zfill(largo)


def generar_txt_f931(
    cuit_empleador: str,
    periodo: str,
    empleados: list[dict],
) -> str:
    """Genera archivo TXT F.931 con registros 1, 2 y 3."""
    lineas = []

    # Registro 1 - Encabezado
    r1 = (
        "01"                                    # tipo registro
        + cuit_empleador.zfill(11)              # CUIT empleador
        + _fmt_fecha_periodo(periodo)           # período
        + str(len(empleados)).zfill(5)          # cantidad de empleados
        + "0".zfill(15)                         # total remuneraciones (se actualiza después)
    )
    lineas.append(r1)

    total_rem = Decimal("0")
    total_aportes = Decimal("0")
    total_contrib = Decimal("0")

    # Registro 2 - Detalle por empleado
    for emp in empleados:
        rem = Decimal(str(emp["remuneracion"]))
        apo = Decimal(str(emp["aportes"]))
        con = Decimal(str(emp["contribuciones"]))
        total_rem += rem
        total_aportes += apo
        total_contrib += con

        r2 = (
            "02"
            + emp["cuit"].zfill(11)
            + _pad(emp["apellido_nombre"], 30)
            + _pad_num(str(rem), 15)
            + _pad_num(str(apo), 15)
            + _pad_num(str(con), 15)
            + emp.get("situacion_revista", "1").zfill(2)
        )
        lineas.append(r2)

    # Registro 3 - Totales
    r3 = (
        "03"
        + cuit_empleador.zfill(11)
        + _fmt_fecha_periodo(periodo)
        + str(len(empleados)).zfill(5)
        + _pad_num(str(total_rem), 15)
        + _pad_num(str(total_aportes), 15)
        + _pad_num(str(total_contrib), 15)
    )
    lineas.append(r3)

    return "\n".join(lineas)
```

- [ ] **Step 4: Run test to verify it passes**
- [ ] **Step 5: Commit**

---

### Task 2: API F.931

**Files:**
- Create: `backend/app/api/f931.py`
- Create: `backend/tests/test_f931_api.py`
- Modify: `backend/app/main.py`

**Interfaces:**
- Consumes: `generar_txt_f931` from Task 1
- Produces: `POST /clientes/{id}/f931/generar` → descarga TXT

- [ ] **Step 1-5:** Implementar router + test + registrar en main.py + commit

---

### Task 3: Convenio Multilateral — atribución por jurisdicción

**Files:**
- Create: `backend/app/convenio/atribucion.py`
- Create: `backend/tests/test_convenio.py`

**Interfaces:**
- Produces: `atribuir_ingresos(ingresos_brutos_por_jurisdiccion) -> dict`, `calcular_coeficientes(atribuciones) -> dict`

Provincias argentinas (24 jurisdicciones + CABA):
```python
PROVINCIAS = [
    "01", "02", "03", "04", "05", "06", "07", "08", "09", "10",
    "11", "12", "13", "14", "15", "16", "17", "18", "19", "20",
    "21", "22", "23", "24", "25",
]
```

- [ ] **Step 1: Write failing test**
- [ ] **Step 2-5:** Implementación + tests + commit

---

### Task 4: API Convenio

**Files:**
- Create: `backend/app/api/convenio.py`
- Create: `backend/tests/test_convenio_api.py`
- Modify: `backend/app/main.py`

**Interfaces:**
- Produces: `POST /clientes/{id}/convenio/cm05` → descarga TXT con atribución

- [ ] **Step 1-5:** Implementar + test + registrar + commit

---

### Task 5: Frontend — Pantallas F.931 y Convenio

**Files:**
- Create: `frontend/src/components/F931.tsx`
- Create: `frontend/src/components/Convenio.tsx`
- Modify: `frontend/src/api.ts`
- Modify: `frontend/src/pages/Home.tsx`

- [ ] **Step 1-3:** Componentes + build + commit

---

### Task 6: Cierre suite + push

- [ ] Run full backend test suite
- [ ] Build frontend
- [ ] Update ESTADO.md
- [ ] Commit + push
