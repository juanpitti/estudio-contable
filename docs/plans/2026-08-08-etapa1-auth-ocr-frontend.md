# Etapa 1 (continuación) — Auth con roles + Pipeline de extracción + Frontend — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use the executing-plans skill. Steps use checkbox (`- [ ]`) syntax.

**Goal:** Login con roles (owner/senior), pipeline Plan 1 (QR → OCR → confianza por campo → "revisar, no inventa") expuesto por API, y frontend React con login + pantalla "subir factura" drag&drop mostrando campos con semáforo de confianza.

**Architecture:** Backend: `app/auth.py` (JWT + pbkdf2 stdlib), `app/extractor/` (qr con cv2, ocr como interfaz enchufable con stub, normalizador con validación CUIT, pipeline con umbral), `app/api/extraccion.py`. Frontend: Vite + React + TS + Tailwind + shadcn en `frontend/` con proxy a `:8000`.

**Tech Stack:** PyJWT, qrcode + opencv-headless (QR, todo wheel puro), FastAPI UploadFile; React 18 + Vite.

## Global Constraints

- Usuarios seed de desarrollo (owner/owner123, senior/senior123) — solo dev, documentado; JWT_SECRET por env.
- QR legible → confianza 1.0 sin OCR (criterio de aceptación del v4).
- Confianza < 0.85 o sin datos → estado "revisar"; el sistema NUNCA inventa valores.
- OCR real (tesseract/LLM fallback) NO va en esta iteración: interfaz lista + stub honesto.
- Frontend y staging solo datos ficticios.

**Interfaces:**
- `app.auth`: `crear_token(sub, rol) -> str`, `decodificar_token(token) -> dict`, `usuario_actual` (dependency), `requerir_rol(*roles)` (dependency factory)
- `app.api.auth`: `POST /auth/login {username, password} -> {access_token, token_type}`
- `app.extractor.tipos`: `CampoExtraido(valor, confianza, fuente)`, `ResultadoExtraccion(campos, estado)`, `UMBRAL_CONFIANZA = 0.85`
- `app.extractor.qr`: `extraer_qr(imagen: bytes) -> dict | None` (decodifica QR AFIP `fe/qr/?p=base64(json)`)
- `app.extractor.normalizador`: `normalizar_qr(payload: dict) -> dict[str, CampoExtraido]`
- `app.extractor.pipeline`: `PipelineExtraccion(ocr=None).procesar(archivo: bytes) -> ResultadoExtraccion`
- `app.api.extraccion`: `POST /extraccion/comprobante` (multipart, requiere token)

---

### Task 1: Auth JWT + roles (TDD)

**Files:** Create `app/auth.py`, `app/api/auth.py`; Modify `app/main.py`, `app/api/clientes.py`, `tests/test_clientes_api.py`; Test `tests/test_auth.py`

- [ ] **Step 1: Test rojo** `test_auth.py`: login ok devuelve token; password mal 401; POST /clientes sin token 401; con token owner 201; token adulterado 401
- [ ] **Step 2:** Correr → FAIL
- [ ] **Step 3:** Implementar `auth.py` (pbkdf2_hmac, PyJWT, HTTPBearer dependency), router `/auth/login`, proteger `/clientes` (lectura: token válido; escritura: owner/senior)
- [ ] **Step 4:** Actualizar `test_clientes_api.py` (fixture autenticada) + correr toda la suite → PASS
- [ ] **Step 5:** Commit `feat(auth): login JWT con roles owner/senior`

### Task 2: Pipeline de extracción QR/OCR (TDD)

**Files:** Create `app/extractor/{__init__,tipos,qr,ocr,normalizador,pipeline}.py`; Test `tests/test_pipeline.py`, `tests/test_qr.py`

- [ ] **Step 1: Test rojo** — QR AFIP generado con `qrcode` (payload real: cuit, ptoVta, tipoCmp, nroCmp, importe, fecha, codAut) → campos exactos, confianza 1.0, fuente "qr", estado "ok"; imagen sin QR → stub OCR → estado "revisar" sin inventar; QR con CUIT inválido → confianza baja → "revisar"; OCR fake baja confianza → "revisar"
- [ ] **Step 2:** Correr → FAIL
- [ ] **Step 3:** Implementar módulos (cv2.QRCodeDetector, base64 JSON AFIP, normalizador con `app.cuit.validar_cuit`)
- [ ] **Step 4:** Correr → PASS
- [ ] **Step 5:** Commit `feat(extractor): pipeline QR→OCR con confianza por campo`

### Task 3: Endpoint de extracción (TDD)

**Files:** Create `app/api/extraccion.py`; Modify `app/main.py`; Test `tests/test_extraccion_api.py`

- [ ] **Step 1: Test rojo** — POST multipart con PNG de QR + token → 200 con campos y estado; sin token → 401
- [ ] **Step 2:** Correr → FAIL
- [ ] **Step 3:** Implementar endpoint y montarlo
- [ ] **Step 4:** Correr suite completa → PASS
- [ ] **Step 5:** Commit `feat(api): POST /extraccion/comprobante`

### Task 4: Frontend React (login + subir factura)

**Files:** Create `frontend/` (scaffold webapp-building); `src/App.tsx`, `src/api.ts`, `src/components/SubirFactura.tsx`, `src/components/Login.tsx`

- [ ] **Step 1:** `init-webapp.sh frontend "Estudio Contable"` + `npm install`
- [ ] **Step 2:** Implementar: login (guarda token), pantalla drag&drop → POST /extraccion/comprobante → tabla de campos con badge de confianza (verde ≥0.85, amarillo 0.5-0.85, rojo <0.5) y banner "REVISAR" cuando aplica
- [ ] **Step 3:** Verificar: `npm run build` exit 0
- [ ] **Step 4:** Commit `feat(frontend): login + subir factura con semáforo de confianza`

### Task 5: Cierre

- [ ] **Step 1:** Suite backend completa verde + build frontend OK (evidencia)
- [ ] **Step 2:** Dev server temporal para validar, luego detenerlo; entregar link de preview
