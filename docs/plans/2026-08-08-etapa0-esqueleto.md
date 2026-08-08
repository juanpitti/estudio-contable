# Etapa 0 (Tarea B) + Fundaciones Etapa 1 — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use the executing-plans skill to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Dejar andando el prototipo WS ARCA (portón de la Etapa 0) y el esqueleto del backend FastAPI con la cartera mínima de clientes, todo con tests verdes y CI configurado.

**Architecture:** Monorepo `estudio-contable/` con `backend/` (FastAPI + paquetes internos `app.arca`, `app.cuit`, `app.api`) y `docs/`. Todo I/O externo (WSAA/wsfe) detrás de clases inyectables para testear sin certificado real. Frontend React y auth JWT quedan para la iteración siguiente (Etapa 1 semanas 2-4).

**Tech Stack:** Python 3.12, FastAPI 0.141, zeep 4.3 (SOAP ARCA), cryptography 47, pytest 9, httpx (TestClient), Docker Compose, GitHub Actions.

## Global Constraints

- Datos de prueba siempre ficticios/anonimizados (Plan v4 regla 2; Ley 25.326).
- Ningún certificado ni CUIT real se commitea al repo.
- TDD estricto: cada módulo nace con su test rojo primero.
- URLs ARCA: homologación por defecto; producción solo por flag de entorno.
- Commits frecuentes, uno por tarea verde.
- Verificación antes de declarar cualquier tarea completa (verification-before-completion).

### Revisión crítica del Plan v4 (hallazgos previos a ejecutar)

1. **Etapa 0 Tarea A (encuesta) y protocolo en competidores son acciones humanas** — no automatizables; quedan para el owner.
2. **RG/DIG ARCA 74/2022: no verificada.** Búsqueda en Biblioteca Electrónica ARCA (2026-08-08) no devuelve esa norma con ese número; puede ser una Disposición interna o número impreciso. Se documenta como pendiente de verificación manual en `docs/etapa0/verificacion-rg-74-2022.md`. **No se asume su contenido.**
3. **El prototipo WS no puede correr end-to-end sin certificado de homologación** (requiere CUIT + clave fiscal del owner). Se entrega testeado unitariamente con transporte mockeado + script CLI listo para correr con certificado real.
4. RG 5824/2026 (vigente para operaciones desde 2026-07-01) agrega obligaciones de emisión que afectan Etapa 4 — anotado para ese momento.

## Estructura de archivos

- Create: `estudio-contable/README.md`, `.gitignore`, `docker-compose.yml`, `.github/workflows/ci.yml`
- Create: `backend/requirements.txt`, `backend/pyproject.toml`, `backend/Dockerfile`
- Create: `backend/app/__init__.py`, `app/main.py`, `app/cuit.py`, `app/models.py`, `app/api/__init__.py`, `app/api/clientes.py`
- Create: `backend/app/arca/__init__.py`, `arca/config.py`, `arca/wsaa.py`, `arca/wsfe.py`
- Create: `backend/tests/test_health.py`, `test_cuit.py`, `test_clientes_api.py`, `test_wsaa.py`, `test_wsfe.py`
- Create: `scripts/etapa0_arca_check.py`
- Create: `docs/etapa0/verificacion-rg-74-2022.md`

**Interfaces:**
- `app.cuit`: `validar_cuit(cuit: str) -> bool`, `formatear_cuit(cuit: str) -> str` (produce `"20-27396523-9"`; consume solo stdlib)
- `app.arca.config`: `ArcaEnv` (enum HOMOLOGACION/PRODUCCION), `WSAA_URLS`, `WSFE_URLS`
- `app.arca.wsaa`: `TicketAcceso(token, sign, expiration)`, `construir_tra(service, ttl=3600) -> bytes`, `firmar_cms(tra, cert_pem, key_pem) -> bytes`, `login(cms, env, client=None) -> TicketAcceso` (zeep inyectable)
- `app.arca.wsfe`: `WsfeClient(cuit, ta, env, client=None)` con `.dummy() -> dict`, `.ultimo_autorizado(pto_vta, cbte_tipo) -> int`, `.consultar_comprobante(cbte_tipo, pto_vta, nro) -> dict`
- `app.api.clientes`: router `/clientes` CRUD sobre repo en memoria; valida CUIT vía `app.cuit`

---

### Task 1: Esqueleto del repo

**Files:**
- Create: `README.md`, `.gitignore`, `.github/workflows/ci.yml`, `backend/requirements.txt`, `backend/pyproject.toml`

- [ ] **Step 1:** Crear archivos de scaffolding (README con decisiones de marco del v4, .gitignore con `*.pem`, `*.key`, `.env`, `__pycache__`, `venv`)
- [ ] **Step 2:** `git init && git add -A && git commit -m "chore: esqueleto inicial del monorepo"`
- [ ] **Step 3:** Verificar: `git log --oneline` muestra 1 commit

### Task 2: Backend mínimo + health check (TDD)

**Files:**
- Create: `backend/app/__init__.py`, `backend/app/main.py`
- Test: `backend/tests/test_health.py`

- [ ] **Step 1: Test rojo** — `test_health.py`:

```python
from fastapi.testclient import TestClient
from app.main import app

def test_health_devuelve_ok_y_version():
    r = TestClient(app).get("/health")
    assert r.status_code == 200
    body = r.json()
    assert body["status"] == "ok"
    assert body["env"] in ("homologacion", "produccion")
```

- [ ] **Step 2: Correr** `cd backend && python -m pytest tests/test_health.py -v` → Expected: FAIL (ModuleNotFoundError: app)
- [ ] **Step 3: Implementar** `app/main.py` con FastAPI(), `/health` leyendo `ARCA_ENV` (default `homologacion`), y montaje del router de clientes
- [ ] **Step 4: Correr** → Expected: PASS
- [ ] **Step 5: Commit** `feat(backend): app FastAPI con /health`

### Task 3: Validador de CUIT (TDD)

**Files:**
- Create: `backend/app/cuit.py`
- Test: `backend/tests/test_cuit.py`

- [ ] **Step 1: Test rojo** — casos con dígito verificador calculado a mano (módulo 11, pesos 5,4,3,2,7,6,5,4,3,2):

```python
import pytest
from app.cuit import validar_cuit, formatear_cuit

def test_cuit_valido_con_guiones():      assert validar_cuit("20-27396523-9") is True
def test_cuit_valido_sin_guiones():      assert validar_cuit("20273965239") is True
def test_digito_verificador_invalido():  assert validar_cuit("20-27396523-0") is False
def test_largo_invalido():               assert validar_cuit("20-2739652-9") is False
def test_no_numerico():                  assert validar_cuit("XX-27396523-9") is False
def test_formatear():                    assert formatear_cuit("20273965239") == "20-27396523-9"
def test_formatear_invalido_lanza():     
    with pytest.raises(ValueError): formatear_cuit("123")
```

- [ ] **Step 2: Correr** → FAIL (ModuleNotFoundError)
- [ ] **Step 3: Implementar** módulo 11: `dv = 11 - (suma % 11)`; 11→0, 10→9
- [ ] **Step 4: Correr** → PASS
- [ ] **Step 5: Commit** `feat(backend): validación de CUIT con dígito verificador`

### Task 4: Módulo WSAA — login ticket (TDD, sin cert real)

**Files:**
- Create: `backend/app/arca/__init__.py`, `backend/app/arca/config.py`, `backend/app/arca/wsaa.py`
- Test: `backend/tests/test_wsaa.py`

- [ ] **Step 1: Test rojo** — TRA bien formado (XML con service, generationTime < expirationTime, uniqueId entero); login parsea token/sign/expiration desde respuesta mockeada; TTL custom:

```python
from datetime import datetime, timezone
from unittest.mock import MagicMock
from app.arca.wsaa import construir_tra, login
from app.arca.config import ArcaEnv

def test_tra_contiene_servicio_y_tiempos_coherentes():
    tra = construir_tra("wsfe", ttl=600)
    assert b"<service>wsfe</service>" in tra
    # generationTime < expirationTime y TTL ~600s (parsear XML)
    ...

def test_login_parsea_ticket(mock_zeep_client):  # client inyectado con loginCms mockeado
    ta = login(b"cms-falso", ArcaEnv.HOMOLOGACION, client=mock_zeep_client)
    assert ta.token == "TOKEN1" and ta.sign == "SIGN1"
```

- [ ] **Step 2: Correr** → FAIL
- [ ] **Step 3: Implementar** `construir_tra` (xml.etree), `firmar_cms` (cryptography.hazmat pkcs7, PEM cert+key), `login` (zeep.Client si no se inyecta; parsea loginCmsReturn XML con token/sign/expirationTime)
- [ ] **Step 4: Correr** → PASS
- [ ] **Step 5: Commit** `feat(arca): WSAA login ticket con TRA firmado`

### Task 5: Módulo WSFE — consultas (TDD, mockeado)

**Files:**
- Create: `backend/app/arca/wsfe.py`
- Test: `backend/tests/test_wsfe.py`

- [ ] **Step 1: Test rojo** — `dummy()` devuelve dict con AppServer/DbServer/AuthServer; `ultimo_autorizado` devuelve int y envía Cuit/token/sign correctos; `consultar_comprobante` mapea campos (cae, fecha, importe):

```python
def test_ultimo_autorizado_devuelve_numero(mock_wsfe_zeep):
    c = WsfeClient(cuit="20273965239", ta=TA_FALSO, env=ArcaEnv.HOMOLOGACION, client=mock_wsfe_zeep)
    assert c.ultimo_autorizado(pto_vta=1, cbte_tipo=6) == 42
    # verificar que el Auth enviado tiene Token/Sign/Cuit correctos
```

- [ ] **Step 2: Correr** → FAIL
- [ ] **Step 3: Implementar** `WsfeClient` con `FECompUltimoAutorizado`, `FECompConsultar`, `FEDummy` sobre zeep inyectable
- [ ] **Step 4: Correr** → PASS
- [ ] **Step 5: Commit** `feat(arca): cliente wsfe con dummy, último autorizado y consulta`

### Task 6: API de clientes — cartera mínima (TDD)

**Files:**
- Create: `backend/app/models.py`, `backend/app/api/__init__.py`, `backend/app/api/clientes.py`
- Test: `backend/tests/test_clientes_api.py`

- [ ] **Step 1: Test rojo** — POST /clientes con CUIT válido → 201; CUIT inválido → 422; GET /clientes lista; GET /clientes/{id} 404; CUIT duplicado → 409:

```python
def test_crear_cliente_cuit_valido(client):
    r = client.post("/clientes", json={"cuit": "20-27396523-9", "razon_social": "Prueba SA", "condicion_iva": "RI"})
    assert r.status_code == 201
    assert r.json()["cuit"] == "20-27396523-9"

def test_crear_cliente_cuit_invalido_422(client): ...
def test_cuit_duplicado_409(client): ...
```

- [ ] **Step 2: Correr** → FAIL
- [ ] **Step 3: Implementar** modelo pydantic `Cliente` (cuit, razon_social, condicion_iva en {RI, MT, EX, CF}), repo en memoria con `Depends` para aislar entre tests
- [ ] **Step 4: Correr** → PASS (incluido 422 por CUIT inválido vía validador del Task 3)
- [ ] **Step 5: Commit** `feat(api): CRUD de clientes con validación de CUIT`

### Task 7: Docker + CI

**Files:**
- Create: `backend/Dockerfile`, `docker-compose.yml`, `.github/workflows/ci.yml`

- [ ] **Step 1:** Dockerfile python:3.12-slim (install requirements, uvicorn), compose con servicios `backend` + `db` (postgres:16) — db sin uso aún, ya cableada para Etapa 1
- [ ] **Step 2:** CI: job `backend-tests` → pip install -r backend/requirements.txt + pytest
- [ ] **Step 3:** Verificar: `python -c "import yaml; yaml.safe_load(open('.github/workflows/ci.yml'))"` y compose parsea (`docker compose config -q` si docker disponible; si no, validación YAML)
- [ ] **Step 4:** Commit `chore: docker compose y CI con pytest`

### Task 8: Docs Etapa 0 + script de portón

**Files:**
- Create: `docs/etapa0/verificacion-rg-74-2022.md`, `scripts/etapa0_arca_check.py`

- [ ] **Step 1:** Doc de verificación: estado "NO VERIFICADA", qué se buscó, dónde, y checklist de verificación manual (Biblioteca Electrónica ARCA, texto de DIG 74/2022, canal lícito de extracción)
- [ ] **Step 2:** Script CLI `etapa0_arca_check.py --cert x.pem --key y.key --cuit N` que corre login WSAA + FEDummy + ultimo_autorizado en homologación e imprime resultado (es el "se testea con el script del prototipo" del v4)
- [ ] **Step 3:** Verificar: `python scripts/etapa0_arca_check.py --help` exit 0
- [ ] **Step 4:** Commit `docs(etapa0): verificación normativa pendiente + script de portón`

### Task 9: Cierre

- [ ] **Step 1:** Suite completa: `cd backend && python -m pytest -v` → 0 failures (verification-before-completion)
- [ ] **Step 2:** Commit final y reporte con evidencia

## Fuera de alcance de este plan (siguiente iteración)

- Auth JWT con roles owner/senior (Etapa 1 semana 2)
- Frontend React + pantalla "subir factura" (Etapa 1 semanas 2-4)
- Pipeline OCR Plan 1 (detector→QR→OCR→normalizador)
- PostgreSQL real (repo en memoria por ahora, interfaz ya inyectable)
