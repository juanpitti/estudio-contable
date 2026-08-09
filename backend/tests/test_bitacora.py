from app.bitacora.modelo import registrar_revision, listar_revisiones, obtener_ultima_revision


def test_registrar_y_listar_revision():
    registrar_revision("liquidacion_iva", 1, "senior@estudio.com", "aprobado", "Todo correcto")
    revs = listar_revisiones("liquidacion_iva", 1)
    assert len(revs) == 1
    assert revs[0].estado == "aprobado"


def test_ultima_revision():
    registrar_revision("liquidacion_iva", 1, "senior@estudio.com", "aprobado", "OK")
    registrar_revision("liquidacion_iva", 1, "owner@estudio.com", "revisado", "Revisión final")
    ultima = obtener_ultima_revision("liquidacion_iva", 1)
    assert ultima is not None
    assert ultima.estado == "revisado"
    assert ultima.usuario == "owner@estudio.com"


def test_listar_vacio():
    revs = listar_revisiones("comprobante", 99)
    assert revs == []
