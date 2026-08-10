"""Aplicación FastAPI principal — plataforma para estudios contables (AR)."""

import os

from fastapi import FastAPI

from app.api.arca import router as arca_router
from app.api.asistente import router as asistente_router
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
from app.database import DATABASE_URL, init_db


def _run_alembic_migrations() -> None:
    """Corre migraciones Alembic si estamos en PostgreSQL."""
    from alembic.config import Config
    from alembic import command

    alembic_cfg = Config("alembic.ini")
    alembic_cfg.set_main_option("sqlalchemy.url", DATABASE_URL)
    command.upgrade(alembic_cfg, "head")


def crear_app() -> FastAPI:
    app = FastAPI(
        title="Estudio Contable API",
        version="0.1.0",
        description="Backend por etapas testeables — Plan v4",
    )

    # Inicializar tablas: Alembic en PostgreSQL, create_all en SQLite (tests/dev)
    if DATABASE_URL.startswith("postgresql"):
        _run_alembic_migrations()
    else:
        init_db()

    from app.seed import seed_usuarios
    seed_usuarios()

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
    app.include_router(asistente_router)

    static_dir = os.environ.get("STATIC_DIR", "static")
    if os.path.isdir(static_dir):
        from fastapi.staticfiles import StaticFiles
        app.mount("/", StaticFiles(directory=static_dir, html=True), name="static")

    return app


app = crear_app()
