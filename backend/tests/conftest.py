import pytest
from sqlalchemy.orm import Session

from app.database import SessionLocal, init_db, engine


@pytest.fixture(autouse=True)
def limpiar_estado_global():
    """Limpia tablas de DB entre tests."""
    from app.bitacora.modelo import _limpiar_revisiones
    _limpiar_revisiones()
    # Limpiar otras tablas
    from sqlalchemy import text
    with engine.begin() as conn:
        conn.execute(text("DELETE FROM lineas_alicuota"))
        conn.execute(text("DELETE FROM comprobantes"))
        conn.execute(text("DELETE FROM clientes"))
    yield
    _limpiar_revisiones()
    with engine.begin() as conn:
        conn.execute(text("DELETE FROM lineas_alicuota"))
        conn.execute(text("DELETE FROM comprobantes"))
        conn.execute(text("DELETE FROM clientes"))


@pytest.fixture
def db_session() -> Session:
    """Sesión de DB para tests (SQLite en memoria con tablas creadas)."""
    init_db()
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
