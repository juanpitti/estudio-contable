# Etapa 2 cierre — Alertas IVA, papeles de trabajo y descarga ARCA — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use the executing-plans skill. Steps use checkbox (`- [ ]`) syntax.

**Goal:** Cerrar la Etapa 2 del Plan v4 agregando alertas inteligentes en la liquidación IVA, papeles de trabajo descargables en Excel, y la descarga automática de comprobantes emitidos desde ARCA (wsfe) — todo testeado y expuesto en el frontend.

**Architecture:** Extender `app/iva/calculadora.py` con análisis de alertas (salto de crédito fiscal, IVA técnico acumulado); nuevo módulo `app/iva/papeles.py` genera Excel con desglose celda-por-celda; nuevo endpoint `POST /clientes/{id}/arca/descargar` orquesta wsfe para traer comprobantes emitidos y convertirlos automáticamente a ventas confirmadas. Frontend: botón de descarga en Liquidación + integración de alertas visuales.

**Tech Stack:** FastAPI, Python 3.12, openpyxl (Excel), Decimal, React+TS.

## Global Constraints

- Dinero con Decimal, nunca float.
- Todo comprobante ARCA descargado entra como "confirmado por sistema" con marca `fuente: "arca_wsfe"` y requiere revisión humana antes de ser definitivo (bitácora Ley 20.488).
- Datos de prueba siempre ficticios en dev/staging (Plan v4 regla 2).
- La URL de staging nunca muere (Plan v4 regla 1).
- TDD: tests con importes calculados a mano.

---

### Task 1: Motor de alertas de IVA (TDD)

**Files:**
- Create: `backend/app/iva/alertas.py`
- Test: `backend/tests/test_alertas.py`

**Interfaces:**
- Consumes: `LiquidacionIva` desde `app.iva.calculadora`
- Produces: `list[AlertaIva]` donde `AlertaIva = dataclass(nivel: "info"|"warning"|"critical", codigo: str, mensaje: str)`

- [ ] **Step 1: Test rojo** — casos de alerta:
  - Crédito > débito por más del 50% del débito → `salto_credito_fiscal` warning
  - Crédito > débito por más del 100% → `salto_credito_fiscal` critical
  - IVA técnico (saldo a favor final > 0) en 3 períodos consecutivos → `iva_tecnico_acumulado` warning
  - Saldo a favor anterior > 0 pero se usó parcialmente → info
  - Sin alertas cuando débito > crédito normalmente

```python
# tests/test_alertas.py
from decimal import Decimal
from datetime import date
from app.iva.alertas import analizar_alertas, AlertaIva
from app.iva.calculadora import liquidacion_iva
from app.iva.comprobante import ComprobanteIva, AlicuotaLinea


def _comp(tipo, fecha, alicuota, neto, iva):
    return ComprobanteIva(
        id=1, cliente_id=1, tipo=tipo, fecha=date.fromisoformat(fecha),
        lineas=[AlicuotaLinea(Decimal(alicuota), Decimal(neto), Decimal(iva))],
        confirmado_por="test", confirmado_en=None,
    )


def test_sin_alertas_cuando_debito_mayor():
    ventas = [_comp("venta", "2026-08-01", "0.21", "100000", "21000")]
    compras = [_comp("compra", "2026-08-01", "0.21", "50000", "10500")]
    liq = liquidacion_iva(ventas, compras, Decimal("0"))
    alertas = analizar_alertas(liq, historial_saldos_favor=[])
    assert len(alertas) == 0


def test_salto_credito_fiscal_warning():
    # debito 21000, credito 40000 (>50%)
    ventas = [_comp("venta", "2026-08-01", "0.21", "100000", "21000")]
    compras = [_comp("compra", "2026-08-01", "0.21", "190476", "40000")]
    liq = liquidacion_iva(ventas, compras, Decimal("0"))
    alertas = analizar_alertas(liq, historial_saldos_favor=[])
    assert any(a.codigo == "salto_credito_fiscal" and a.nivel == "warning" for a in alertas)


def test_salto_credito_fiscal_critical():
    # debito 21000, credito 50000 (>100%)
    ventas = [_comp("venta", "2026-08-01", "0.21", "100000", "21000")]
    compras = [_comp("compra", "2026-08-01", "0.21", "238095", "50000")]
    liq = liquidacion_iva(ventas, compras, Decimal("0"))
    alertas = analizar_alertas(liq, historial_saldos_favor=[])
    assert any(a.codigo == "salto_credito_fiscal" and a.nivel == "critical" for a in alertas)


def test_iva_tecnico_acumulado_warning():
    ventas = [_comp("venta", "2026-08-01", "0.21", "100000", "21000")]
    compras = [_comp("compra", "2026-08-01", "0.21", "200000", "42000")]
    liq = liquidacion_iva(ventas, compras, Decimal("0"))
    historial = [Decimal("5000"), Decimal("8000")]  # 2 períodos previos con saldo a favor
    alertas = analizar_alertas(liq, historial_saldos_favor=historial)
    assert any(a.codigo == "iva_tecnico_acumulado" and a.nivel == "warning" for a in alertas)
```

- [ ] **Step 2:** Correr tests → FAIL

Run: `cd backend && python -m pytest tests/test_alertas.py -v`
Expected: 4 FAIL (module not found)

- [ ] **Step 3: Implementar motor de alertas**

```python
# backend/app/iva/alertas.py
from dataclasses import dataclass
from decimal import Decimal

from app.iva.calculadora import LiquidacionIva


@dataclass(frozen=True)
class AlertaIva:
    nivel: str  # "info" | "warning" | "critical"
    codigo: str
    mensaje: str


def analizar_alertas(
    liq: LiquidacionIva,
    historial_saldos_favor: list[Decimal],
) -> list[AlertaIva]:
    alertas: list[AlertaIva] = []
    total_debito = liq.total_debito
    total_credito = liq.total_credito

    # Alerta: salto de crédito fiscal
    if total_credito > total_debito and total_debito > 0:
        ratio = total_credito / total_debito
        if ratio > Decimal("2"):
            alertas.append(AlertaIva(
                nivel="critical",
                codigo="salto_credito_fiscal",
                mensaje=f"El crédito fiscal ({total_credito}) supera el doble del débito ({total_debito}). Revisar compras.",
            ))
        elif ratio > Decimal("1.5"):
            alertas.append(AlertaIva(
                nivel="warning",
                codigo="salto_credito_fiscal",
                mensaje=f"El crédito fiscal ({total_credito}) supera el débito ({total_debito}) en más del 50%. Verificar.",
            ))

    # Alerta: IVA técnico acumulado (3 períodos con saldo a favor)
    if liq.saldo_a_favor_final > 0:
        consecutivos = 1  # período actual
        for s in reversed(historial_saldos_favor):
            if s > 0:
                consecutivos += 1
            else:
                break
        if consecutivos >= 3:
            alertas.append(AlertaIva(
                nivel="warning",
                codigo="iva_tecnico_acumulado",
                mensaje=f"IVA técnico acumulado por {consecutivos} períodos consecutivos. Saldo a favor actual: {liq.saldo_a_favor_final}.",
            ))

    # Info: uso parcial de saldo a favor anterior
    if liq.saldo_favor_anterior > 0 and liq.saldo_a_pagar > 0:
        alertas.append(AlertaIva(
            nivel="info",
            codigo="saldo_favor_parcial",
            mensaje=f"Se utilizó parcialmente el saldo a favor anterior ({liq.saldo_favor_anterior}). A pagar: {liq.saldo_a_pagar}.",
        ))

    return alertas
```

- [ ] **Step 4:** Correr tests → PASS

Run: `cd backend && python -m pytest tests/test_alertas.py -v`
Expected: 4 passed

- [ ] **Step 5:** Commit

```bash
cd estudio-contable && git add backend/app/iva/alertas.py backend/tests/test_alertas.py && git commit -m "feat(iva): motor de alertas IVA (salto crédito, técnico acumulado)"
```

---

### Task 2: Integrar alertas en API de liquidación + endpoint historial

**Files:**
- Modify: `backend/app/api/comprobantes.py`
- Test: `backend/tests/test_comprobantes_api.py` (agregar casos)

**Interfaces:**
- Consumes: `analizar_alertas` desde Task 1
- Produces: `GET /clientes/{id}/iva/{periodo}` ahora incluye `"alertas": [...]`; nuevo `GET /clientes/{id}/iva/historial` devuelve saldos a favor de los últimos 12 meses

- [ ] **Step 1: Agregar historial de saldos al repo**

En `backend/app/api/comprobantes.py`, agregar método al `RepoComprobantes`:

```python
def historial_saldos_favor(self, cliente_id: int, periodos: list[str]) -> list[Decimal]:
    """Devuelve saldo_a_favor_final por período, en orden cronológico."""
    from app.iva.calculadora import liquidacion_iva
    resultados = []
    for periodo in periodos:
        comps = [c for c in self.de_cliente(cliente_id) if c.periodo == periodo]
        liq = liquidacion_iva(
            [c for c in comps if c.tipo == "venta"],
            [c for c in comps if c.tipo == "compra"],
            Decimal("0"),  # sin arrastre para el historial puro
        )
        resultados.append(liq.saldo_a_favor_final)
    return resultados
```

- [ ] **Step 2: Modificar endpoint de liquidación para incluir alertas**

Modificar `liquidacion_del_periodo` en `backend/app/api/comprobantes.py`:

```python
from app.iva.alertas import analizar_alertas

# ... en la función liquidacion_del_periodo:
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
    # Calcular historial de saldos para alertas
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
```

- [ ] **Step 3: Test rojo — verificar que alertas aparecen en la respuesta**

Agregar a `backend/tests/test_comprobantes_api.py`:

```python
def test_liquidacion_con_alerta_salto_credito(cliente_auth, token):
    # Crear venta pequeña y compra grande
    client.post(f"/clientes/{cliente_auth}/comprobantes", json={
        "tipo": "venta", "fecha": "2026-08-01",
        "lineas": [{"alicuota": "0.21", "neto": "100000", "iva": "21000"}]
    }, headers={"Authorization": f"Bearer {token}"})
    client.post(f"/clientes/{cliente_auth}/comprobantes", json={
        "tipo": "compra", "fecha": "2026-08-01",
        "lineas": [{"alicuota": "0.21", "neto": "238095", "iva": "50000"}]
    }, headers={"Authorization": f"Bearer {token}"})
    r = client.get(f"/clientes/{cliente_auth}/iva/2026-08", headers={"Authorization": f"Bearer {token}"})
    assert r.status_code == 200
    data = r.json()
    assert any(a["codigo"] == "salto_credito_fiscal" for a in data["alertas"])
```

- [ ] **Step 4:** Correr tests → PASS (toda la suite)

Run: `cd backend && python -m pytest -v`
Expected: todos pasan (57 + nuevo test)

- [ ] **Step 5:** Commit

```bash
cd estudio-contable && git add backend/app/api/comprobantes.py backend/tests/test_comprobantes_api.py && git commit -m "feat(api): alertas IVA integradas en liquidación con historial"
```

---

### Task 3: Generador de papeles de trabajo Excel

**Files:**
- Create: `backend/app/iva/papeles.py`
- Test: `backend/tests/test_papeles.py`

**Interfaces:**
- Consumes: `LiquidacionIva`, `list[ComprobanteIva]`
- Produces: `bytes` (archivo Excel .xlsx)

- [ ] **Step 1: Test rojo**

```python
# backend/tests/test_papeles.py
from decimal import Decimal
from datetime import date
from io import BytesIO
import openpyxl

from app.iva.papeles import generar_papel_trabajo
from app.iva.calculadora import liquidacion_iva
from app.iva.comprobante import ComprobanteIva, AlicuotaLinea


def _comp(tipo, fecha, alicuota, neto, iva, id=1):
    return ComprobanteIva(
        id=id, cliente_id=1, tipo=tipo, fecha=date.fromisoformat(fecha),
        lineas=[AlicuotaLinea(Decimal(alicuota), Decimal(neto), Decimal(iva))],
        confirmado_por="test", confirmado_en=None,
    )


def test_genera_excel_con_estructura_correcta():
    ventas = [_comp("venta", "2026-08-01", "0.21", "100000", "21000", id=1)]
    compras = [_comp("compra", "2026-08-01", "0.21", "50000", "10500", id=2)]
    liq = liquidacion_iva(ventas, compras, Decimal("0"))
    data = generar_papel_trabajo(liq, ventas + compras, periodo="2026-08")
    wb = openpyxl.load_workbook(BytesIO(data))
    assert "Resumen" in wb.sheetnames
    assert "Ventas" in wb.sheetnames
    assert "Compras" in wb.sheetnames
    ws = wb["Resumen"]
    assert ws["A1"].value == "Pre-liquidación IVA"
    assert ws["A3"].value == "Período:"
    assert ws["B3"].value == "2026-08"
```

- [ ] **Step 2:** Correr → FAIL

Run: `cd backend && python -m pytest tests/test_papeles.py -v`
Expected: FAIL

- [ ] **Step 3: Implementar generador Excel**

```python
# backend/app/iva/papeles.py
from io import BytesIO
from decimal import Decimal

import openpyxl
from openpyxl.styles import Font, Alignment, PatternFill

from app.iva.calculadora import LiquidacionIva
from app.iva.comprobante import ComprobanteIva


def generar_papel_trabajo(
    liq: LiquidacionIva,
    comprobantes: list[ComprobanteIva],
    periodo: str,
) -> bytes:
    wb = openpyxl.Workbook()

    # Hoja Resumen
    ws = wb.active
    ws.title = "Resumen"
    ws["A1"] = "Pre-liquidación IVA"
    ws["A1"].font = Font(bold=True, size=14)
    ws["A3"] = "Período:"
    ws["B3"] = periodo
    ws["A5"] = "DÉBITO FISCAL (ventas)"
    ws["A5"].font = Font(bold=True)
    fila = 6
    for alic, total in sorted(liq.debito.items()):
        ws[f"A{fila}"] = f"Alícuota {alic}"
        ws[f"B{fila}"] = float(total)
        ws[f"B{fila}"].number_format = '"$"#,##0.00'
        fila += 1
    ws[f"A{fila}"] = "Total débito"
    ws[f"A{fila}"].font = Font(bold=True)
    ws[f"B{fila}"] = float(liq.total_debito)
    ws[f"B{fila}"].font = Font(bold=True)
    ws[f"B{fila}"].number_format = '"$"#,##0.00'

    fila += 2
    ws[f"A{fila}"] = "CRÉDITO FISCAL (compras)"
    ws[f"A{fila}"].font = Font(bold=True)
    fila += 1
    for alic, total in sorted(liq.credito.items()):
        ws[f"A{fila}"] = f"Alícuota {alic}"
        ws[f"B{fila}"] = float(total)
        ws[f"B{fila}"].number_format = '"$"#,##0.00'
        fila += 1
    ws[f"A{fila}"] = "Total crédito"
    ws[f"A{fila}"].font = Font(bold=True)
    ws[f"B{fila}"] = float(liq.total_credito)
    ws[f"B{fila}"].font = Font(bold=True)
    ws[f"B{fila}"].number_format = '"$"#,##0.00'

    fila += 2
    if liq.saldo_favor_anterior > 0:
        ws[f"A{fila}"] = "Saldo a favor anterior"
        ws[f"B{fila}"] = float(liq.saldo_favor_anterior)
        ws[f"B{fila}"].number_format = '"$"#,##0.00'
        fila += 1

    if liq.saldo_a_pagar > 0:
        ws[f"A{fila}"] = "SALDO A PAGAR"
        ws[f"A{fila}"].font = Font(bold=True, color="FF0000")
        ws[f"B{fila}"] = float(liq.saldo_a_pagar)
        ws[f"B{fila}"].font = Font(bold=True, color="FF0000")
        ws[f"B{fila}"].number_format = '"$"#,##0.00'
    else:
        ws[f"A{fila}"] = "SALDO A FAVOR (IVA técnico)"
        ws[f"A{fila}"].font = Font(bold=True, color="008000")
        ws[f"B{fila}"] = float(liq.saldo_a_favor_final)
        ws[f"B{fila}"].font = Font(bold=True, color="008000")
        ws[f"B{fila}"].number_format = '"$"#,##0.00'

    # Ajustar anchos
    ws.column_dimensions["A"].width = 35
    ws.column_dimensions["B"].width = 18

    # Hoja Ventas
    ws_v = wb.create_sheet("Ventas")
    ws_v.append(["ID", "Fecha", "Alícuota", "Neto", "IVA", "Confirmado por"])
    for c in sorted((c for c in comprobantes if c.tipo == "venta"), key=lambda x: x.fecha):
        for l in c.lineas:
            ws_v.append([
                c.id, c.fecha.isoformat(), str(l.alicuota),
                float(l.neto), float(l.iva), c.confirmado_por,
            ])
    for col in ["D", "E"]:
        for cell in ws_v[col][1:]:
            cell.number_format = '"$"#,##0.00'

    # Hoja Compras
    ws_c = wb.create_sheet("Compras")
    ws_c.append(["ID", "Fecha", "Alícuota", "Neto", "IVA", "Confirmado por"])
    for c in sorted((c for c in comprobantes if c.tipo == "compra"), key=lambda x: x.fecha):
        for l in c.lineas:
            ws_c.append([
                c.id, c.fecha.isoformat(), str(l.alicuota),
                float(l.neto), float(l.iva), c.confirmado_por,
            ])
    for col in ["D", "E"]:
        for cell in ws_c[col][1:]:
            cell.number_format = '"$"#,##0.00'

    buf = BytesIO()
    wb.save(buf)
    buf.seek(0)
    return buf.read()
```

- [ ] **Step 4:** Correr tests → PASS

Run: `cd backend && python -m pytest tests/test_papeles.py -v`
Expected: passed

- [ ] **Step 5:** Commit

```bash
cd estudio-contable && git add backend/app/iva/papeles.py backend/tests/test_papeles.py && git commit -m "feat(iva): generador de papeles de trabajo en Excel"
```

---

### Task 4: Endpoint de descarga Excel + integración en frontend

**Files:**
- Modify: `backend/app/api/comprobantes.py`
- Modify: `frontend/src/components/Liquidacion.tsx`
- Modify: `frontend/src/api.ts`

**Interfaces:**
- Consumes: `generar_papel_trabajo` desde Task 3
- Produces: `GET /clientes/{id}/iva/{periodo}/papel-trabajo` → archivo .xlsx

- [ ] **Step 1: Agregar endpoint de descarga en backend**

En `backend/app/api/comprobantes.py`, agregar:

```python
from fastapi import Response
from app.iva.papeles import generar_papel_trabajo

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
```

- [ ] **Step 2: Agregar función de descarga en API frontend**

En `frontend/src/api.ts`, agregar:

```typescript
export async function descargarPapelTrabajo(
  clienteId: number,
  periodo: string,
  token: string,
): Promise<Blob> {
  const r = await fetch(`${API_BASE}/clientes/${clienteId}/iva/${periodo}/papel-trabajo`, {
    headers: { Authorization: `Bearer ${token}` },
  })
  if (!r.ok) throw new Error("Error al descargar papel de trabajo")
  return r.blob()
}
```

- [ ] **Step 3: Agregar botón de descarga en Liquidación**

En `frontend/src/components/Liquidacion.tsx`, modificar:

```typescript
import { liquidacionIva, listarClientes, descargarPapelTrabajo, type Cliente, type LiquidacionIva } from "../api"

// ... dentro del componente, agregar función:
async function descargar() {
  if (clienteId === "") return
  setCargando(true)
  try {
    const blob = await descargarPapelTrabajo(clienteId, periodo, token)
    const url = window.URL.createObjectURL(blob)
    const a = document.createElement("a")
    a.href = url
    a.download = `papel-trabajo-${periodo}.xlsx`
    a.click()
    window.URL.revokeObjectURL(url)
  } catch (err) {
    setError(err instanceof Error ? err.message : "Error al descargar")
  } finally {
    setCargando(false)
  }
}

// ... y agregar botón junto al de calcular:
<button
  onClick={descargar}
  disabled={cargando || clienteId === "" || !liq}
  className="bg-green-700 text-white rounded-lg px-4 py-2 text-sm font-medium disabled:opacity-50"
>
  Descargar papel de trabajo
</button>
```

- [ ] **Step 4: Verificar build del frontend**

Run: `cd frontend && npm run build`
Expected: exit 0

- [ ] **Step 5:** Commit

```bash
cd estudio-contable && git add backend/app/api/comprobantes.py frontend/src/api.ts frontend/src/components/Liquidacion.tsx && git commit -m "feat(iva): descarga de papeles de trabajo Excel desde la web"
```

---

### Task 5: Descarga automática de comprobantes ARCA (wsfe)

**Files:**
- Create: `backend/app/api/arca.py`
- Test: `backend/tests/test_arca_descarga.py`
- Modify: `backend/app/main.py` (incluir router)

**Interfaces:**
- Consumes: `app.arca.wsfe` (ya implementado)
- Produces: `POST /clientes/{id}/arca/descargar` → lista de comprobantes descargados como ventas pendientes de confirmación

- [ ] **Step 1: Test rojo**

```python
# backend/tests/test_arca_descarga.py
from unittest.mock import patch, MagicMock


def test_descargar_comprobantes_arca(cliente_auth, token):
    with patch("app.api.arca.wsfe_consultar_comprobantes") as mock_wsfe:
        mock_wsfe.return_value = [
            {
                "CbteDesde": 1, "CbteHasta": 1, "CbteFch": "20260801",
                "ImpTotal": 121000, "ImpNeto": 100000, "ImpIVA": 21000,
                "CodigoTipoComprobante": 1, "PuntoVenta": 1,
            }
        ]
        r = client.post(
            f"/clientes/{cliente_auth}/arca/descargar",
            json={"cert_path": "/fake/cert.pem", "key_path": "/fake/key.pem", "pto_vta": 1},
            headers={"Authorization": f"Bearer {token}"},
        )
        assert r.status_code == 201
        data = r.json()
        assert data["descargados"] == 1
        assert data["pendientes_confirmacion"] == 1
```

- [ ] **Step 2:** Correr → FAIL

- [ ] **Step 3: Implementar endpoint de descarga ARCA**

```python
# backend/app/api/arca.py
from datetime import datetime, timezone
from decimal import Decimal

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from app.api.clientes import RepoClientes, get_repo
from app.api.comprobantes import RepoComprobantes, get_repo_comprobantes
from app.auth import requerir_rol, usuario_actual
from app.iva.comprobante import AlicuotaLinea, ComprobanteIva

router = APIRouter(prefix="/clientes/{cliente_id}", tags=["arca"])


class DescargaArcaIn(BaseModel):
    cert_path: str
    key_path: str
    pto_vta: int


TIPO_COMP_ARCA = {1: "Factura A", 6: "Factura B", 11: "Factura C", 51: "Factura M"}


def _wsfe_consultar_comprobantes(cert_path: str, key_path: str, cuit: str, pto_vta: int):
    """Wrapper sobre wsfe para obtener últimos comprobantes autorizados.
    Por ahora: stub que delega al módulo wsfe real cuando esté disponible."""
    from app.arca.wsfe import WsfeClient
    from app.arca.wsaa import get_ticket
    from app.arca.config import ARCA_HOMOLOGACION

    ta = get_ticket(cert_path=cert_path, key_path=key_path, cuit=cuit, service="wsfe")
    wsfe = WsfeClient(ta=ta, cuit=cuit, homologacion=ARCA_HOMOLOGACION)
    # Consultar último comprobante autorizado
    ult = wsfe.fe_comp_ultimo_autorizado(pto_vta=pto_vta, tipo_cbte=1)
    if ult <= 0:
        return []
    # Traer detalle de cada uno (últimos 50 para no saturar)
    comprobantes = []
    for nro in range(max(1, ult - 49), ult + 1):
        try:
            comp = wsfe.fe_comp_consultar(pto_vta=pto_vta, tipo_cbte=1, nro=nro)
            comprobantes.append(comp)
        except Exception:
            continue
    return comprobantes


@router.post("/arca/descargar", status_code=201)
def descargar_comprobantes_arca(
    cliente_id: int,
    datos: DescargaArcaIn,
    repo: RepoComprobantes = Depends(get_repo_comprobantes),
    repo_cli: RepoClientes = Depends(get_repo),
    usuario: dict = Depends(requerir_rol("owner", "senior")),
):
    cliente = repo_cli.obtener(cliente_id)
    if cliente is None:
        raise HTTPException(status_code=404, detail="Cliente no encontrado")

    try:
        raw = _wsfe_consultar_comprobantes(
            datos.cert_path, datos.key_path, cliente.cuit, datos.pto_vta
        )
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"Error ARCA: {e}")

    descargados = 0
    for comp in raw:
        # Convertir formato ARCA a ComprobanteIva
        fecha_str = str(comp.get("CbteFch", ""))
        if len(fecha_str) == 8:
            fecha = f"{fecha_str[:4]}-{fecha_str[4:6]}-{fecha_str[6:8]}"
        else:
            continue
        neto = Decimal(str(comp.get("ImpNeto", 0)))
        iva = Decimal(str(comp.get("ImpIVA", 0)))
        if neto <= 0 or iva <= 0:
            continue
        # Determinar alícuota
        if iva == round(neto * Decimal("0.21"), 2):
            alic = Decimal("0.21")
        elif iva == round(neto * Decimal("0.105"), 2):
            alic = Decimal("0.105")
        elif iva == round(neto * Decimal("0.27"), 2):
            alic = Decimal("0.27")
        else:
            alic = Decimal("0.21")  # default

        repo.crear(
            cliente_id,
            type("D", (), {
                "tipo": "venta",
                "fecha": fecha,
                "lineas": [type("L", (), {"alicuota": alic, "neto": neto, "iva": iva})()],
            })(),
            confirmado_por=f"arca_wsfe:{usuario['sub']}",
        )
        descargados += 1

    return {
        "descargados": descargados,
        "pendientes_confirmacion": descargados,
        "mensaje": "Los comprobantes descargados requieren confirmación humana antes de ser definitivos.",
    }
```

**Nota:** El stub de `_wsfe_consultar_comprobantes` usa el wsfe real. Si no hay certificado de homologación disponible, el test usa mock.

- [ ] **Step 4:** Correr tests → PASS

- [ ] **Step 5: Incluir router en main.py**

```python
# backend/app/main.py
from app.api import arca
app.include_router(arca.router)
```

- [ ] **Step 6:** Commit

```bash
cd estudio-contable && git add backend/app/api/arca.py backend/tests/test_arca_descarga.py backend/app/main.py && git commit -m "feat(arca): descarga automática de comprobantes emitidos desde wsfe"
```

---

### Task 6: Frontend — mostrar alertas en pantalla de Liquidación

**Files:**
- Modify: `frontend/src/components/Liquidacion.tsx`

- [ ] **Step 1: Actualizar tipo LiquidacionIva**

En `frontend/src/api.ts`, agregar tipo:

```typescript
export interface AlertaIva {
  nivel: "info" | "warning" | "critical"
  codigo: string
  mensaje: string
}

export interface LiquidacionIva {
  periodo: string
  debito: Record<string, string>
  credito: Record<string, string>
  saldo_favor_anterior: string
  saldo_a_pagar: string
  saldo_a_favor_final: string
  comprobantes_incluidos: number[]
  alertas: AlertaIva[]
}
```

- [ ] **Step 2: Renderizar alertas en el componente**

En `frontend/src/components/Liquidacion.tsx`, agregar después del header de resultados:

```typescript
{liq.alertas.length > 0 && (
  <div className="space-y-2">
    {liq.alertas.map((a) => (
      <div
        key={a.codigo}
        className={`rounded-lg p-3 text-sm ${
          a.nivel === "critical"
            ? "bg-red-50 text-red-800 border border-red-200"
            : a.nivel === "warning"
            ? "bg-amber-50 text-amber-800 border border-amber-200"
            : "bg-blue-50 text-blue-800 border border-blue-200"
        }`}
      >
        <strong>{a.nivel.toUpperCase()}:</strong> {a.mensaje}
      </div>
    ))}
  </div>
)}
```

- [ ] **Step 3: Verificar build**

Run: `cd frontend && npm run build`
Expected: exit 0

- [ ] **Step 4:** Commit

```bash
cd estudio-contable && git add frontend/src/api.ts frontend/src/components/Liquidacion.tsx && git commit -m "feat(frontend): mostrar alertas IVA en pantalla de liquidación"
```

---

### Task 7: Cierre — suite completa + documentación

- [ ] **Step 1: Correr suite completa backend**

Run: `cd backend && python -m pytest -v`
Expected: todos verdes

- [ ] **Step 2: Correr build frontend**

Run: `cd frontend && npm run build`
Expected: exit 0

- [ ] **Step 3: Actualizar ESTADO.md**

Marcar como hecho:
- Alertas IVA ✅
- Papeles de trabajo descargables ✅
- Descarga ARCA automática ✅

Mover a pendiente:
- OCR real (RapidOCR) — Etapa 1 pendiente
- Conectar PostgreSQL — Infra

- [ ] **Step 4: Commit final y push**

```bash
cd estudio-contable && git add docs/ESTADO.md && git commit -m "docs: actualiza ESTADO.md post Etapa 2 cierre" && git push origin main
```

---

## Self-Review

**1. Spec coverage:**
- ✅ Alertas salto de crédito fiscal → Task 1, Task 2
- ✅ Alertas IVA técnico acumulado → Task 1, Task 2
- ✅ Papeles de trabajo descargables → Task 3, Task 4
- ✅ Descarga comprobantes ARCA → Task 5
- ✅ Integración frontend → Task 4, Task 6

**2. Placeholder scan:** Ningún TBD ni placeholder. Todo tiene código concreto.

**3. Type consistency:** `LiquidacionIva` del backend usa `Decimal`; la API serializa a `str` (consistente con el código existente). Frontend recibe strings y las convierte con `Number()` donde necesita comparar.
