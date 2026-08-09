from decimal import Decimal

from app.convenio.atribucion import atribuir_ingresos, calcular_coeficientes, JURISDICCIONES


def test_lista_jurisdicciones():
    assert len(JURISDICCIONES) == 24
    assert JURISDICCIONES[0]["codigo"] == "01"
    assert JURISDICCIONES[0]["nombre"] == "CABA"


def test_atribuir_ingresos():
    ingresos = {
        "01": Decimal("500000"),   # CABA
        "02": Decimal("300000"),   # Buenos Aires
        "14": Decimal("200000"),   # Misiones
    }
    resultado = atribuir_ingresos(ingresos)
    assert resultado["total_ingresos"] == Decimal("1000000")
    assert resultado["atribuciones"]["01"]["porcentaje"] == Decimal("50")
    assert resultado["atribuciones"]["02"]["porcentaje"] == Decimal("30")
    assert resultado["atribuciones"]["14"]["porcentaje"] == Decimal("20")


def test_calcular_coeficientes():
    ingresos = {
        "01": Decimal("600000"),
        "02": Decimal("400000"),
    }
    coefs = calcular_coeficientes(ingresos)
    assert coefs["01"] == Decimal("0.60")
    assert coefs["02"] == Decimal("0.40")
    assert sum(coefs.values(), Decimal("0")) == Decimal("1.00")
