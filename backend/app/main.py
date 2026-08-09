"""Aplicación FastAPI principal — plataforma para estudios contables (AR)."""

import os

from fastapi import FastAPI

from app.api.arca import router as arca_router
from app.api.auth import router as auth_router
from app.api.clientes import router as clientes_router
from app.api.comprobantes import router as comprobantes_router
from app.api.extraccion import router as extraccion_router


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
    return app


app = crear_app()
