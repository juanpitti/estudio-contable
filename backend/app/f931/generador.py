"""Generador de TXT F.931 para SICOSS / Declaración en Línea ARCA."""

from decimal import Decimal


def _fmt_fecha_periodo(periodo: str) -> str:
    """Periodo AAAAMM → AAAAMMDD (día 01)."""
    return periodo + "01"


def _pad(texto: str, largo: int) -> str:
    return (texto or "")[:largo].ljust(largo)


def _pad_num(numero: str, largo: int, decimales: int = 2) -> str:
    """Formatea número para TXT SICOSS: sin punto decimal, relleno con ceros."""
    d = Decimal(str(numero))
    entero = int(d)
    frac = int((d - entero) * (10 ** decimales))
    s = f"{entero}{frac:0{decimales}d}"
    return s.zfill(largo)


def generar_txt_f931(
    cuit_empleador: str,
    periodo: str,
    empleados: list[dict],
) -> str:
    """Genera archivo TXT F.931 con registros 1, 2 y 3."""
    lineas = []

    # Registro 1 - Encabezado
    r1 = (
        "01"
        + cuit_empleador.zfill(11)
        + _fmt_fecha_periodo(periodo)
        + str(len(empleados)).zfill(5)
        + "0".zfill(15)
    )
    lineas.append(r1)

    total_rem = Decimal("0")
    total_aportes = Decimal("0")
    total_contrib = Decimal("0")

    for emp in empleados:
        rem = Decimal(str(emp["remuneracion"]))
        apo = Decimal(str(emp["aportes"]))
        con = Decimal(str(emp["contribuciones"]))
        total_rem += rem
        total_aportes += apo
        total_contrib += con

        r2 = (
            "02"
            + emp["cuit"].zfill(11)
            + _pad(emp["apellido_nombre"], 30)
            + _pad_num(str(rem), 15)
            + _pad_num(str(apo), 15)
            + _pad_num(str(con), 15)
            + emp.get("situacion_revista", "1").zfill(2)
        )
        lineas.append(r2)

    r3 = (
        "03"
        + cuit_empleador.zfill(11)
        + _fmt_fecha_periodo(periodo)
        + str(len(empleados)).zfill(5)
        + _pad_num(str(total_rem), 15)
        + _pad_num(str(total_aportes), 15)
        + _pad_num(str(total_contrib), 15)
    )
    lineas.append(r3)

    return "\n".join(lineas)
