from decimal import Decimal

from app.monotributo.categoria import categoria_para_ingresos, proyeccion_categoria, alerta_proximidad_techo


def test_categoria_a_para_ingresos_minimos():
    cat = categoria_para_ingresos(Decimal("1000000"))
    assert cat is not None
    assert cat.codigo == "A"


def test_categoria_k_para_techo_maximo():
    cat = categoria_para_ingresos(Decimal("126610838.75"))
    assert cat is not None
    assert cat.codigo == "K"


def test_excede_techo_maximo():
    cat = categoria_para_ingresos(Decimal("200000000"))
    assert cat is None


def test_proyeccion_mantiene_categoria():
    res = proyeccion_categoria([Decimal("500000")] * 6, "A")
    assert res["categoria_proyectada"] == "A"
    assert res["porcentaje_del_techo"] < 50


def test_proyeccion_supera_techo_actual():
    res = proyeccion_categoria([Decimal("1300000")] * 10, "A")
    assert res["categoria_proyectada"] == "B"
    assert res["alerta"] is True


def test_alerta_proximidad_techo_90_porciento():
    alerta = alerta_proximidad_techo(Decimal("10808469.40"), "A")
    assert alerta is not None
    assert alerta["nivel"] == "warning"


def test_sin_alerta_por_debajo():
    alerta = alerta_proximidad_techo(Decimal("6000000"), "A")
    assert alerta is None
