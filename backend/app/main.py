"""Aplicación FastAPI principal — plataforma para estudios contables (AR)."""

import os

from fastapi import FastAPI

from app.api.arca import router as arca_router
from app.api.auth import router as auth_router
from app.api.bitacora import router as bitacora_router
from app.api.clientes import router as clientes_router
from app.api.comprobantes import router as comprobantes_router
from app.api.conciliacion import router as conciliacion_router
from app.api.convenio import router as convenio_cm_router
from app.api.dashboard import router as dashboard_router
from app.api.extraccion import router as extraccion_router
from app.api.f931 import router as f931_router
from app.api.facturacion import router as facturacion_router
from app.api.monotributo import router as monotributo_router
from app.api.monitor import router as monitor_router


def crear_app() -> FastAPI:
    app = FastAPI(
        title="Estudio Contable API",
        version="0.1.0",
        description="Backend por etapas testeables — Plan v4",
    )

    @app.get("/health")
    def health() -> dict:
        env = os.environ.get("ARCA_ENV", "homologacion")
        return {"status": "ok", "env": env}

    app.include_router(auth_router)
    app.include_router(clientes_router)
    app.include_router(extraccion_router)
    app.include_router(comprobantes_router)
    app.include_router(arca_router)
    app.include_router(conciliacion_router)
    app.include_router(facturacion_router)
    app.include_router(monotributo_router)
    app.include_router(bitacora_router)
    app.include_router(dashboard_router)
    app.include_router(f931_router)
    app.include_router(convenio_cm_router)
    app.include_router(monitor_router)
    return app


app = crear_app()
