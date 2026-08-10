"""Configuración de base de datos — PostgreSQL en producción, SQLite en tests.

La app lee DATABASE_URL del entorno. Si no está definida, usa SQLite en
memoria (útil para tests y desarrollo sin PostgreSQL).
"""

import os

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker
from sqlalchemy.pool import StaticPool

DATABASE_URL = os.environ.get(
    "DATABASE_URL",
    "sqlite:///:memory:",  # default: in-memory para tests
)

if DATABASE_URL.startswith("sqlite"):
    engine = create_engine(
        DATABASE_URL,
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
        pool_pre_ping=True,
    )
else:
    engine = create_engine(DATABASE_URL, pool_pre_ping=True)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


class Base(DeclarativeBase):
    pass


def get_db():
    """Generador de sesiones para FastAPI Depends."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db() -> None:
    """Crea todas las tablas (útil para primer arranque o tests)."""
    Base.metadata.create_all(bind=engine)
