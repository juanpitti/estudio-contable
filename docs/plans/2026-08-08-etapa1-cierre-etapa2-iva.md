# Etapa 1 cierre + Etapa 2 inicio — Cartera web, confirmación humana y calculadora IVA — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use the executing-plans skill. Steps use checkbox (`- [ ]`) syntax.

**Goal:** Pantalla de cartera de clientes en el frontend, confirmación humana de extracciones (bitácora: quién confirmó), y el núcleo de dominio de la Etapa 2: calculadora de IVA por alícuota con saldos de arrastre, expuesta por API y visible en pantalla de Liquidación.

**Architecture:** Backend: `app/iva/` (comprobante, calculadora pura con Decimal), `app/api/comprobantes.py` (ingesta confirmada por usuario + liquidación por período). Frontend: navegación por tabs (Subir factura / Clientes / Liquidación), botón "Confirmar e ingresar" tras extracción OK.

**Tech Stack:** Decimal (dinero exacto), FastAPI, React.

## Global Constraints

- Dinero con Decimal, nunca float, en la calculadora.
- Todo comprobante ingresa SOLO por confirmación humana (bitácora: usuario + timestamp, Ley 20.488 / Plan v4 regla 6).
- La liquidación muestra celda-por-celda de dónde salió cada número (débito/crédito por alícuota + comprobantes incluidos).
- IVA técnico: crédito > débito → saldo a favor del contribuyente (arrastre), jamás negativo a pagar.
- TDD: importes de tests calculados a mano.

**Interfaces:**
- `app.iva.comprobante`: `ComprobanteIva(cliente_id, tipo: "venta"|"compra", fecha, lineas: [AlicuotaLinea(alicuota: Decimal, neto: Decimal, iva: Decimal)], confirmado_por: str, confirmado_en: datetime, id: int)`
- `app.iva.calculadora`: `liquidacion_iva(ventas, compras, saldo_favor_anterior: Decimal) -> LiquidacionIva` con `.debito`, `.credito` (dict alícuota→Decimal), `.saldo_a_pagar`, `.saldo_a_favor_final`
- `app.api.comprobantes`: `POST /clientes/{id}/comprobantes`, `GET /clientes/{id}/comprobantes`, `GET /clientes/{id}/iva/{periodo}` (YYYY-MM) — todo con token; la confirmación requiere owner/senior

---

### Task 1: Calculadora de IVA pura (TDD)

**Files:** Create `app/iva/__init__.py`, `app/iva/comprobante.py`, `app/iva/calculadora.py`; Test `tests/test_iva.py`

- [ ] **Step 1: Test rojo** — casos a mano: débito 21000 (neto 100000 @21%) − crédito 10500 (50000 @21%) = 10500 a pagar; crédito > débito → saldo a favor 9000 y a pagar 0 (IVA técnico); saldo favor anterior 5000 → a pagar 5500; alícuotas 10.5% y 27% desglosadas; período filtra comprobantes
- [ ] **Step 2:** Correr → FAIL
- [ ] **Step 3:** Implementar con Decimal
- [ ] **Step 4:** Correr → PASS
- [ ] **Step 5:** Commit `feat(iva): calculadora de liquidación por alícuota`

### Task 2: API de comprobantes + liquidación (TDD)

**Files:** Create `app/api/comprobantes.py`; Modify `app/main.py`; Test `tests/test_comprobantes_api.py`

- [ ] **Step 1: Test rojo** — POST comprobante con token → 201 y registra `confirmado_por`; sin token 401; GET iva/2026-08 devuelve débito/crédito exactos y la lista de comprobantes incluidos; cliente inexistente 404
- [ ] **Step 2:** Correr → FAIL
- [ ] **Step 3:** Implementar repo en memoria + endpoints (filtrar por período YYYY-MM)
- [ ] **Step 4:** Correr suite → PASS
- [ ] **Step 5:** Commit `feat(api): ingesta confirmada de comprobantes + liquidación IVA`

### Task 3: Frontend — cartera + confirmación + liquidación

**Files:** Modify `frontend/src/pages/Home.tsx`, `src/api.ts`; Create `src/components/Clientes.tsx`, `src/components/Liquidacion.tsx`; Modify `src/components/SubirFactura.tsx` (botón confirmar)

- [ ] **Step 1:** Tabs de navegación; Clientes: tabla + form de alta (CUIT validado por backend, 422 visible); SubirFactura: tras "ok", form mínimo (cliente, tipo venta/compra, neto) + botón "Confirmar e ingresar" que POSTea; Liquidacion: selector cliente + mes → desglose débito/crédito por alícuota y resultado
- [ ] **Step 2:** Verificar `npm run build` exit 0 + smoke test con servidores temporales
- [ ] **Step 3:** Commit `feat(frontend): cartera, confirmación humana y pantalla de liquidación`

### Task 4: Cierre

- [ ] **Step 1:** Suite completa verde + build OK (evidencia)
- [ ] **Step 2:** Reporte + link de preview
