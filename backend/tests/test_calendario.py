from datetime import date

from app.calendario.vencimientos import proximos_vencimientos, vencimientos_del_mes, alertas_vencimientos_proximos


def test_vencimientos_del_mes_tiene_iva():
    vencs = vencimientos_del_mes(2026, 8)
    assert any(v.impuesto == "IVA" for v in vencs)


def test_alertas_detecta_vencimiento_proximo():
    alertas = alertas_vencimientos_proximos(hoy=date(2026, 8, 8), dias_ventana=20)
    assert any(a["impuesto"] == "IVA" for a in alertas)


def test_proximos_vencimientos_limitados():
    vencs = proximos_vencimientos(dias=7, hoy=date(2026, 8, 8))
    assert len(vencs) <= 5
