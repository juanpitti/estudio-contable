# Estado del proyecto — handoff de contexto

> Snapshot al 2026-08-09. Punto de entrada para cualquier sesión nueva: leer esto + el README + `docs/plans/`. Punto de entrada para cualquier sesión nueva: leer esto + el README + `docs/plans/`.

## Qué es

Plataforma web para estudios contables argentinos, desarrollada por etapas testeables según el **Plan v4** (`../Plan de Desarrollo por Etapas Testeables (v4).md` en el workspace padre). Diferencial: extracción de comprobantes con QR/OCR + confianza por campo. Blindaje legal: revisión humana con bitácora (Ley 20.488), solo canales lícitos ARCA, datos ficticios en dev/staging.

## Repo y convenciones

- **GitHub:** https://github.com/juanpitti/estudio-contable (público, rama `main`, CI con pytest en cada push)
- **Local:** `C:\Users\Juan\Documents\kimi\workspace\estudio-contable`
- **Convención:** cada punto terminado → commit + push a `main`.
- **gh CLI portable:** `../gh-cli/bin/gh.exe` (autenticado como juanpitti).
- **Obsidian:** nota del proyecto en `Obsidian Vault/02-Proyectos/Estudio Contable.md`.
- **Proceso de trabajo:** skills instaladas en Kimi Work — `writing-plans` → `executing-plans` → `test-driven-development` → `systematic-debugging` → `requesting-code-review` → `verification-before-completion`. Planes en `docs/plans/`.

## Hecho (100+ tests backend verdes)

| Módulo | Archivos | Notas |
|---|---|---|
| Auth JWT + roles | `backend/app/auth.py`, `api/auth.py` | owner/senior, seeds dev owner/owner123, senior/senior123 |
| Clientes | `app/cuit.py`, `api/clientes.py` | CUIT módulo 11, 409 duplicado, repo en memoria |
| ARCA WSAA/wsfe | `app/arca/` | homologación por defecto, transporte inyectable, script portón `scripts/etapa0_arca_check.py` |
| Extracción Plan 1 | `app/extractor/` | QR AFIP real (confianza 1.0); OCR = **stub** (dice "revisar", no inventa) |
| IVA — Calculadora | `app/iva/calculadora.py`, `app/iva/comprobante.py` | Decimal, alícuotas 21/10.5/27, IVA técnico con arrastre |
| IVA — Alertas | `app/iva/alertas.py` | salto crédito fiscal (warning/critical), IVA técnico acumulado, info saldo favor parcial |
| IVA — Papeles Excel | `app/iva/papeles.py` | genera .xlsx con hojas Resumen/Ventas/Compras, formato moneda ARS |
| API Comprobantes | `app/api/comprobantes.py` | POST/GET comprobantes, liquidación con alertas, descarga Excel `/iva/{p}/papel-trabajo` |
| ARCA Descarga | `app/api/arca.py` | stub listo para wsfe; requiere certificado de homologación del cliente |
| **Conciliación bancaria** | `app/conciliacion/` | **Etapa 3 completa**: parser CSV genérico, deduplicador, motor match 4 niveles (exacto/monto+fecha/rango/aproximado), endpoint `POST /conciliacion/importar` |
| **Facturación con CAE** | `app/facturacion/` | **Etapa 4 completa**: emisión A/B/C/M + NC/ND vía WSFE, PDF con QR, endpoint `/clientes/{id}/facturacion/emitir` |
| **Monotributo** | `app/monotributo/` | **Etapa 5**: categorías AFIP A-K (datos oficiales 08/2026), proyección de categoría, alerta de proximidad al techo (≥80% warning, ≥95% critical), endpoint `/clientes/{id}/monotributo` |
| **Bitácora de revisión** | `app/bitacora/` | **Etapa 5**: trazabilidad Ley 20.488, endpoints POST/GET `/revisiones` |
| **Calendario fiscal** | `app/calendario/` | **Etapa 5**: vencimientos IVA, monotributo, Ganancias, Bienes Personales, recategorización; alertas por proximidad |
| **Dashboard** | `app/api/dashboard.py` | **Etapa 5**: endpoint `/dashboard` con semáforos de cartera (verde/amarillo/rojo), vencimientos próximos, alertas |
| Frontend | `frontend/` | React+TS+Tailwind; login, subir factura (semáforo), Clientes, **Facturación**, **Monotributo**, **Dashboard**, Liquidación IVA (alertas + descarga Excel), Conciliación bancaria (CSV + % match + diferencias); `npm run dev` levanta ambos servidores |
| Infra | docker-compose, `.github/workflows/ci.yml` | PostgreSQL cableada pero SIN conectar |

| Módulo | Archivos | Notas |
|---|---|---|
| Auth JWT + roles | `backend/app/auth.py`, `api/auth.py` | owner/senior, seeds dev owner/owner123, senior/senior123 |
| Clientes | `app/cuit.py`, `api/clientes.py` | CUIT módulo 11, 409 duplicado, repo en memoria |
| ARCA WSAA/wsfe | `app/arca/` | homologación por defecto, transporte inyectable, script portón `scripts/etapa0_arca_check.py` |
| Extracción Plan 1 | `app/extractor/` | QR AFIP real (confianza 1.0); OCR = **stub** (dice "revisar", no inventa) |
| IVA — Calculadora | `app/iva/calculadora.py`, `app/iva/comprobante.py` | Decimal, alícuotas 21/10.5/27, IVA técnico con arrastre |
| IVA — Alertas | `app/iva/alertas.py` | salto crédito fiscal (warning/critical), IVA técnico acumulado, info saldo favor parcial |
| IVA — Papeles Excel | `app/iva/papeles.py` | genera .xlsx con hojas Resumen/Ventas/Compras, formato moneda ARS |
| API Comprobantes | `app/api/comprobantes.py` | POST/GET comprobantes, liquidación con alertas, descarga Excel `/iva/{p}/papel-trabajo` |
| ARCA Descarga | `app/api/arca.py` | stub listo para wsfe; requiere certificado de homologación del cliente |
| **Conciliación bancaria** | `app/conciliacion/` | **Etapa 3 completa**: parser CSV genérico, deduplicador, motor match 4 niveles (exacto/monto+fecha/rango/aproximado), endpoint `POST /conciliacion/importar` |
| Frontend | `frontend/` | React+TS+Tailwind; login, subir factura (semáforo), Clientes, Liquidación IVA (alertas + descarga Excel), **Conciliación bancaria (CSV + % match + diferencias)**; `npm run dev` levanta ambos servidores |
| Infra | docker-compose, `.github/workflows/ci.yml` | PostgreSQL cableada pero SIN conectar |

## Pendiente inmediato (cola priorizada)

1. **Etapa 6:** F.931 y Convenio Multilateral (Semanas 21-24) — Plan 7 + Plan 8
2. **Etapa 7:** Monitor fiscal y asistente IA (Semanas 25-30) — Plan 11 + Plan 13
3. **OCR real:** RapidOCR (onnxruntime, pip puro) detrás de `app/extractor/ocr.py` + fallback LLM. Prueba de aceptación v4: 20 facturas, ≥90% campos críticos.
4. **Conectar PostgreSQL** (persistencia; hoy cada reinicio limpia todo).
5. **Descarga ARCA end-to-end:** cuando esté disponible certificado de homologación, activar `_wsfe_consultar_comprobantes` en `app/api/arca.py`.

1. **OCR real:** RapidOCR (onnxruntime, pip puro) detrás de `app/extractor/ocr.py` + fallback LLM. Prueba de aceptación v4: 20 facturas, ≥90% campos críticos.
2. **Conectar PostgreSQL** (persistencia; hoy cada reinicio limpia todo).
3. **Descarga ARCA end-to-end:** cuando esté disponible certificado de homologación, activar `_wsfe_consultar_comprobantes` en `app/api/arca.py`.
4. **Etapa 4:** Facturación con CAE (Plan 9). Hito comercial: desde acá el producto ya se le puede mostrar a un estudio piloto.

## Bloqueos / no verificado

- ⚠️ **RG/DIG ARCA 74/2022 no verificada** (no existe con ese número en Biblioteca Electrónica). Checklist manual: `docs/etapa0/verificacion-rg-74-2022.md`. Mientras tanto: solo WS oficiales con certificado del cliente.
- ⚠️ Portón ARCA end-to-end espera certificado de homologación del owner (WSASS).
- ⚠️ Etapa 0 Tarea A (encuesta, cliente cero) es acción humana pendiente.
- RG 5824/2026 (operaciones desde 2026-07-01) agrega obligaciones que afectan Etapa 4 (facturación CAE).

## Lecciones del entorno (ahorrar tiempo en próximas sesiones)

- `npm` en Git Bash requiere shim (`~/bin/npm` → `npm.cmd`); node v24, npm 11.
- `kill` de bash no mata procesos Windows: usar `taskkill //PID <pid> //F` (buscar PID con `netstat -ano | grep LISTENING`).
- No dejar uvicorn viejo corriendo: causa 404/500 fantasma en el proxy de Vite.
- Commits git: identidad local configurada (Juan / juan@localhost); rama `main`.
- Cuidado con edits parciales en archivos con imports: pueden duplicarse. Preferir `Write` completo cuando hay riesgo de duplicación.
