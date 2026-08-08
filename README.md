# Estudio Contable — Plataforma web para estudios contables (AR)

Aplicación web desarrollada por etapas testeables según el **Plan de Desarrollo v4**.
Cada etapa termina con funcionalidad real desplegable. Staging solo con datos ficticios o
anonimizados (Ley 25.326); los datos fiscales reales viven en la instalación del estudio.

## Decisiones de marco (del Plan v4)

1. App web desde el día 1; la URL de staging siempre viva.
2. Semana 0 / Etapa 0 como portón: validación + prototipo WS ARCA.
3. Descargadores solo por canales lícitos verificados (ver `docs/etapa0/verificacion-rg-74-2022.md`).
4. Posicionamiento B2B: el contador revisa y firma; bitácora de revisión humana.
5. Diferencial visible: OCR de papel/fotos/tickets con confianza por campo (Etapa 1).
6. Privacidad como arquitectura: contenedores Docker, self-hostable.
7. Table stakes: facturación con CAE, calendario, multi-cliente, importación ARCA.

## Stack

- **Backend:** FastAPI (Python 3.12) — `backend/`
- **Motor:** paquetes internos `app.arca` (WSAA/wsfe), `app.cuit`, `app.api`
- **DB:** PostgreSQL (docker-compose) — cableada desde Etapa 1
- **Frontend:** React + TypeScript + Tailwind — iteración siguiente
- **CI:** GitHub Actions (pytest en cada push)

## Desarrollo

```bash
cd backend
pip install -r requirements.txt
python -m pytest -v                 # tests
uvicorn app.main:app --reload       # API en http://localhost:8000 (docs en /docs)
```

## Prototipo Etapa 0 (portón ARCA)

Requiere certificado de homologación (WSASS) propio — nunca se commitea:

```bash
python scripts/etapa0_arca_check.py --cert cert.pem --key key.pem --cuit 20273965239
```

## Roadmap

Etapa 0 portón → 1 esqueleto + OCR → 2 ingesta ARCA + IVA → 3 conciliación →
4 facturación CAE → 5 cartera/monotributo → 6 F.931 + CM → 7 monitor + asistente.
