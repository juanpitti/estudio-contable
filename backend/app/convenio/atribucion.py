"""Modelo de atribución de ingresos para Convenio Multilateral."""

from decimal import Decimal


JURISDICCIONES: list[dict] = [
    {"codigo": "01", "nombre": "CABA"},
    {"codigo": "02", "nombre": "Buenos Aires"},
    {"codigo": "03", "nombre": "Catamarca"},
    {"codigo": "04", "nombre": "Córdoba"},
    {"codigo": "05", "nombre": "Corrientes"},
    {"codigo": "06", "nombre": "Chaco"},
    {"codigo": "07", "nombre": "Chubut"},
    {"codigo": "08", "nombre": "Entre Ríos"},
    {"codigo": "09", "nombre": "Formosa"},
    {"codigo": "10", "nombre": "Jujuy"},
    {"codigo": "11", "nombre": "La Pampa"},
    {"codigo": "12", "nombre": "La Rioja"},
    {"codigo": "13", "nombre": "Mendoza"},
    {"codigo": "14", "nombre": "Misiones"},
    {"codigo": "15", "nombre": "Neuquén"},
    {"codigo": "16", "nombre": "Río Negro"},
    {"codigo": "17", "nombre": "Salta"},
    {"codigo": "18", "nombre": "San Juan"},
    {"codigo": "19", "nombre": "San Luis"},
    {"codigo": "20", "nombre": "Santa Cruz"},
    {"codigo": "21", "nombre": "Santa Fe"},
    {"codigo": "22", "nombre": "Santiago del Estero"},
    {"codigo": "23", "nombre": "Tucumán"},
    {"codigo": "24", "nombre": "Tierra del Fuego"},
]


def atribuir_ingresos(ingresos_por_jurisdiccion: dict[str, Decimal]) -> dict:
    """Distribuye ingresos brutos por jurisdicción y calcula porcentajes."""
    total = sum(ingresos_por_jurisdiccion.values(), Decimal("0"))
    if total == 0:
        return {"total_ingresos": Decimal("0"), "atribuciones": {}}

    atribuciones = {}
    for codigo, ingreso in ingresos_por_jurisdiccion.items():
        porcentaje = (ingreso / total * 100).quantize(Decimal("0.01"))
        atribuciones[codigo] = {
            "ingreso": str(ingreso),
            "porcentaje": porcentaje,
        }

    return {
        "total_ingresos": total,
        "atribuciones": atribuciones,
    }


def calcular_coeficientes(ingresos_por_jurisdiccion: dict[str, Decimal]) -> dict[str, Decimal]:
    """Calcula coeficientes de distribución para CM05."""
    total = sum(ingresos_por_jurisdiccion.values(), Decimal("0"))
    if total == 0:
        return {}

    coefs = {}
    for codigo, ingreso in ingresos_por_jurisdiccion.items():
        coefs[codigo] = (ingreso / total).quantize(Decimal("0.01"))

    return coefs
