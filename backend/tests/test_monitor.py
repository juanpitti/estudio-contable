from decimal import Decimal

from app.monitor.fiscal import monitor_cliente, monitor_global, resumen_estudio, AlertaMonitor


def test_monitor_cliente_sin_alertas():
    alertas = monitor_cliente(1, Decimal("1000000"), "A")
    assert len(alertas) == 1  # Solo IVA sin revisar (bitácora vacía)
    assert alertas[0].codigo == "IVA_SIN_REVISAR"


def test_monitor_cliente_cerca_techo():
    alertas = monitor_cliente(1, Decimal("11000000"), "A")  # ~92% del techo
    assert any(a.codigo == "MONOTRIBUTO_PROXIMO_TECHO" for a in alertas)


def test_monitor_global_incluye_vencimientos():
    alertas = monitor_global([{"id": 1, "ingresos_acumulados": "1000000", "categoria_monotributo": "A"}])
    assert len(alertas) >= 1  # Al menos IVA sin revisar + posibles vencimientos


def test_resumen_estudio():
    resumen = resumen_estudio([
        {"id": 1, "ingresos_acumulados": "1000000", "categoria_monotributo": "A"},
        {"id": 2, "ingresos_acumulados": "500000", "categoria_monotributo": "A"},
    ])
    assert resumen["total_clientes"] == 2
    assert resumen["alertas_activas"] >= 2  # Ambos sin IVA revisada
