import pytest


@pytest.fixture(autouse=True)
def limpiar_estado_global():
    """Limpia estado mutable en memoria entre tests."""
    from app.bitacora.modelo import _limpiar_revisiones
    _limpiar_revisiones()
    yield
    _limpiar_revisiones()
