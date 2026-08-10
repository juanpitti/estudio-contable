import pytest
from sqlalchemy.orm import Session

from app.bitacora.modelo import RepoRevisiones


@pytest.fixture
def repo(db_session: Session):
    return RepoRevisiones(db_session)


def test_registrar_y_listar_revision(repo):
    repo.registrar("liquidacion_iva", 1, "senior@estudio.com", "aprobado", "Todo correcto")
    revs = repo.listar("liquidacion_iva", 1)
    assert len(revs) == 1
    assert revs[0].estado == "aprobado"


def test_ultima_revision(repo):
    repo.registrar("liquidacion_iva", 1, "senior@estudio.com", "aprobado", "OK")
    repo.registrar("liquidacion_iva", 1, "owner@estudio.com", "revisado", "Revisión final")
    ultima = repo.obtener_ultima("liquidacion_iva", 1)
    assert ultima is not None
    assert ultima.estado == "revisado"
    assert ultima.usuario == "owner@estudio.com"


def test_listar_vacio(repo):
    revs = repo.listar("comprobante", 99)
    assert revs == []
