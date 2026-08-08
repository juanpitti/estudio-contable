import pytest

from app.cuit import formatear_cuit, validar_cuit

# Dígitos verificadores calculados a mano (módulo 11, pesos 5,4,3,2,7,6,5,4,3,2):
# 20-27396523-?: suma=167, 167%11=2, dv=11-2=9
# 23-00000000-?: suma=22, 22%11=0, dv=11 -> 0
# 26-00000000-?: suma=34, 34%11=1, dv=10 -> 9


def test_cuit_valido_con_guiones():
    assert validar_cuit("20-27396523-9") is True


def test_cuit_valido_sin_guiones():
    assert validar_cuit("20273965239") is True


def test_cuit_valido_dv_once_mapea_a_cero():
    assert validar_cuit("23-00000000-0") is True


def test_cuit_valido_dv_diez_mapea_a_nueve():
    assert validar_cuit("26-00000000-9") is True


def test_digito_verificador_invalido():
    assert validar_cuit("20-27396523-0") is False


def test_largo_invalido():
    assert validar_cuit("20-2739652-9") is False


def test_no_numerico():
    assert validar_cuit("XX-27396523-9") is False


def test_formatear():
    assert formatear_cuit("20273965239") == "20-27396523-9"


def test_formatear_invalido_lanza():
    with pytest.raises(ValueError):
        formatear_cuit("123")
