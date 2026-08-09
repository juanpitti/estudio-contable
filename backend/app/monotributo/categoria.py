"""Modelo de categorías de monotributo AFIP."""

from dataclasses import dataclass
from decimal import Decimal


@dataclass(frozen=True)
class Categoria:
    codigo: str
    ingresos_brutos_max: Decimal
    impuesto_integrado: Decimal
    aportes_sipa: Decimal
    obra_social: Decimal

    @property
    def total_mensual(self) -> Decimal:
        return self.impuesto_integrado + self.aportes_sipa + self.obra_social


CATEGORIAS: list[Categoria] = [
    Categoria("A", Decimal("12009410.45"), Decimal("5585.77"), Decimal("5585.77"), Decimal("18246.86")),
    Categoria("B", Decimal("17595182.74"), Decimal("10612.98"), Decimal("10612.98"), Decimal("20071.55")),
    Categoria("C", Decimal("24670494.31"), Decimal("18246.86"), Decimal("16757.32"), Decimal("22078.71")),
    Categoria("D", Decimal("30628651.43"), Decimal("29790.79"), Decimal("27742.67"), Decimal("24286.58")),
    Categoria("E", Decimal("36028231.33"), Decimal("55857.73"), Decimal("44313.79"), Decimal("26715.24")),
    Categoria("F", Decimal("45151659.41"), Decimal("78573.20"), Decimal("57719.64"), Decimal("29386.76")),
    Categoria("G", Decimal("53995798.87"), Decimal("142995.76"), Decimal("71497.87"), Decimal("41141.46")),
    Categoria("H", Decimal("81924660.37"), Decimal("409623.31"), Decimal("204811.64"), Decimal("57598.04")),
    Categoria("I", Decimal("91699761.90"), Decimal("814591.79"), Decimal("325836.71"), Decimal("80637.26")),
    Categoria("J", Decimal("105012519.20"), Decimal("977510.14"), Decimal("391004.07"), Decimal("112892.16")),
    Categoria("K", Decimal("126610838.75"), Decimal("1368514.20"), Decimal("456171.40"), Decimal("158049.02")),
]


def categoria_para_ingresos(ingresos_anuales: Decimal) -> Categoria | None:
    """Devuelve la categoría correspondiente a los ingresos brutos anuales."""
    for cat in CATEGORIAS:
        if ingresos_anuales <= cat.ingresos_brutos_max:
            return cat
    return None


def proyeccion_categoria(ingresos_mensuales: list[Decimal], categoria_actual: str) -> dict:
    """Proyecta la categoría basándose en ingresos acumulados."""
    acumulado = sum(ingresos_mensuales, Decimal("0"))
    cat_actual = next((c for c in CATEGORIAS if c.codigo == categoria_actual), CATEGORIAS[0])
    cat_proyectada = categoria_para_ingresos(acumulado) or CATEGORIAS[-1]
    porcentaje = (acumulado / cat_actual.ingresos_brutos_max * 100).quantize(Decimal("0.01"))
    return {
        "categoria_actual": categoria_actual,
        "categoria_proyectada": cat_proyectada.codigo,
        "ingresos_acumulados": str(acumulado),
        "techo_actual": str(cat_actual.ingresos_brutos_max),
        "porcentaje_del_techo": float(porcentaje),
        "alerta": cat_proyectada.codigo != categoria_actual or porcentaje >= Decimal("90"),
    }


def alerta_proximidad_techo(ingresos_acumulados: Decimal, categoria_actual: str) -> dict | None:
    """Genera alerta si se acerca al techo de la categoría (≥80% warning, ≥95% critical)."""
    cat = next((c for c in CATEGORIAS if c.codigo == categoria_actual), None)
    if not cat:
        return None
    porcentaje = (ingresos_acumulados / cat.ingresos_brutos_max * 100).quantize(Decimal("0.01"))
    if porcentaje >= Decimal("95"):
        return {
            "nivel": "critical",
            "codigo": "MONOTRIBUTO_CERCA_TECHO",
            "mensaje": f"Estás al {porcentaje}% del techo de la categoría {categoria_actual}. Recategorización urgente.",
        }
    if porcentaje >= Decimal("80"):
        return {
            "nivel": "warning",
            "codigo": "MONOTRIBUTO_PROXIMO_TECHO",
            "mensaje": f"Estás al {porcentaje}% del techo de la categoría {categoria_actual}. Considerá recategorizar.",
        }
    return None
