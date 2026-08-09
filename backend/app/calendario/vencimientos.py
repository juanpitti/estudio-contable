"""Calendario de vencimientos fiscales argentinos."""

from dataclasses import dataclass
from datetime import date, timedelta


@dataclass(frozen=True)
class Vencimiento:
    impuesto: str
    fecha: date
    periodicidad: str


_VENCIMIENTOS_BASE: list[Vencimiento] = [
    Vencimiento("IVA", date(2026, 1, 21), "mensual"),
    Vencimiento("IVA", date(2026, 2, 21), "mensual"),
    Vencimiento("IVA", date(2026, 3, 21), "mensual"),
    Vencimiento("IVA", date(2026, 4, 21), "mensual"),
    Vencimiento("IVA", date(2026, 5, 21), "mensual"),
    Vencimiento("IVA", date(2026, 6, 23), "mensual"),
    Vencimiento("IVA", date(2026, 7, 21), "mensual"),
    Vencimiento("IVA", date(2026, 8, 21), "mensual"),
    Vencimiento("IVA", date(2026, 9, 21), "mensual"),
    Vencimiento("IVA", date(2026, 10, 21), "mensual"),
    Vencimiento("IVA", date(2026, 11, 23), "mensual"),
    Vencimiento("IVA", date(2026, 12, 21), "mensual"),
    Vencimiento("Monotributo", date(2026, 1, 20), "mensual"),
    Vencimiento("Monotributo", date(2026, 2, 20), "mensual"),
    Vencimiento("Monotributo", date(2026, 3, 20), "mensual"),
    Vencimiento("Monotributo", date(2026, 4, 20), "mensual"),
    Vencimiento("Monotributo", date(2026, 5, 20), "mensual"),
    Vencimiento("Monotributo", date(2026, 6, 22), "mensual"),
    Vencimiento("Monotributo", date(2026, 7, 21), "mensual"),
    Vencimiento("Monotributo", date(2026, 8, 20), "mensual"),
    Vencimiento("Monotributo", date(2026, 9, 21), "mensual"),
    Vencimiento("Monotributo", date(2026, 10, 20), "mensual"),
    Vencimiento("Monotributo", date(2026, 11, 20), "mensual"),
    Vencimiento("Monotributo", date(2026, 12, 21), "mensual"),
    Vencimiento("Ganancias PF", date(2026, 6, 15), "anual"),
    Vencimiento("Bienes Personales", date(2026, 6, 15), "anual"),
    Vencimiento("Recategorización Monotributo", date(2026, 1, 20), "semestral"),
    Vencimiento("Recategorización Monotributo", date(2026, 7, 20), "semestral"),
]


def proximos_vencimientos(dias: int = 30, hoy: date | None = None) -> list[Vencimiento]:
    hoy = hoy or date.today()
    limite = hoy + timedelta(days=dias)
    return [v for v in _VENCIMIENTOS_BASE if hoy <= v.fecha <= limite]


def vencimientos_del_mes(anio: int, mes: int) -> list[Vencimiento]:
    return [v for v in _VENCIMIENTOS_BASE if v.fecha.year == anio and v.fecha.month == mes]


def alertas_vencimientos_proximos(hoy: date | None = None, dias_ventana: int = 7) -> list[dict]:
    hoy = hoy or date.today()
    proximos = proximos_vencimientos(dias=dias_ventana, hoy=hoy)
    alertas = []
    for v in proximos:
        dias_restantes = (v.fecha - hoy).days
        nivel = "critical" if dias_restantes <= 3 else "warning" if dias_restantes <= 7 else "info"
        alertas.append({
            "impuesto": v.impuesto,
            "fecha": v.fecha.isoformat(),
            "dias_restantes": dias_restantes,
            "nivel": nivel,
            "mensaje": f"{v.impuesto} vence el {v.fecha.isoformat()} ({dias_restantes} días)",
        })
    return alertas
