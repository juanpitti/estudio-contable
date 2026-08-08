"""Validación y formateo de CUIT/CUIL (módulo 11, RG AFIP)."""

PESOS = (5, 4, 3, 2, 7, 6, 5, 4, 3, 2)


def _solo_digitos(cuit: str) -> str:
    return "".join(c for c in cuit if c.isdigit())


def digito_verificador(base10: str) -> int:
    """Calcula el DV esperado para los primeros 10 dígitos."""
    suma = sum(int(d) * p for d, p in zip(base10, PESOS))
    dv = 11 - (suma % 11)
    if dv == 11:
        return 0
    if dv == 10:
        return 9
    return dv


def validar_cuit(cuit: str) -> bool:
    digitos = _solo_digitos(cuit)
    if len(digitos) != 11:
        return False
    return digito_verificador(digitos[:10]) == int(digitos[10])


def formatear_cuit(cuit: str) -> str:
    """Devuelve 'XX-XXXXXXXX-X'. Lanza ValueError si no es válido."""
    digitos = _solo_digitos(cuit)
    if len(digitos) != 11 or not validar_cuit(digitos):
        raise ValueError(f"CUIT inválido: {cuit!r}")
    return f"{digitos[:2]}-{digitos[2:10]}-{digitos[10]}"
