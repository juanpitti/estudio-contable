"""Aplicación FastAPI principal — plataforma para estudios contables (AR)."""

import os

from fastapi import FastAPI

from app.api.clientes import router as clientes_router


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

    app.include_router(clientes_router)
    return app


app = crear_app()
