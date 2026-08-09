from app.asistente.motor import responder


def test_responder_iva_sin_revisar():
    clientes = [
        {"id": 1, "razon_social": "Alpha", "semaforo": "amarillo"},
        {"id": 2, "razon_social": "Beta", "semaforo": "verde"},
    ]
    r = responder("¿qué clientes tienen la IVA sin revisar?", clientes, [], [])
    assert "Alpha" in r.texto
    assert "Beta" not in r.texto
    assert r.fuente == "bitácora de revisiones"


def test_responder_total_clientes():
    r = responder("¿cuántos clientes tengo?", [{"id": 1}, {"id": 2}, {"id": 3}], [], [])
    assert "3 clientes" in r.texto
    assert r.fuente == "base de clientes"


def test_responder_vencimientos():
    vencs = [{"impuesto": "IVA", "fecha": "2026-08-21", "dias_restantes": 5}]
    r = responder("¿qué vence pronto?", [], [], vencs)
    assert "IVA" in r.texto
    assert r.fuente == "calendario fiscal"


def test_responder_desconocida():
    r = responder("¿qué hora es?", [], [], [])
    assert "No entendí" in r.texto
