"""Parser genérico de movimientos bancarios desde CSV."""

import csv
from datetime import datetime
from decimal import Decimal
from io import StringIO
from typing import Literal

from app.conciliacion.movimiento import MovimientoBancario


def _normalizar_header(h: str) -> str:
    return h.strip().lower().replace("á", "a").replace("é", "e").replace("í", "i").replace("ó", "o").replace("ú", "u")


def _detectar_columnas(headers: list[str]) -> dict[str, int]:
    """Mapea índices de columnas reconocidas."""
    norm = [_normalizar_header(h) for h in headers]
    mapeo = {}
    for i, h in enumerate(norm):
        if h in ("fecha", "fecha de operacion", "fecha operacion", "fecha oper.", "fechas"):
            mapeo["fecha"] = i
        if h in ("descripcion", "concepto", "descrip.", "detalle", "descripción", "movimiento", "descripciones"):
            mapeo["descripcion"] = i
        if h in ("debito", "debe", "importe debido", "cargo", "egreso", "debitos"):
            mapeo["debito"] = i
        if h in ("credito", "haber", "importe acreditado", "abono", "ingreso", "creditos"):
            mapeo["credito"] = i
    if "descripcion" not in mapeo and len(headers) > 1:
        mapeo["descripcion"] = 1  # fallback: segunda columna
    return mapeo


def _parsear_monto(v: str, formato: Literal["es_AR", "en_US"]) -> Decimal | None:
    v = v.strip()
    if not v:
        return None
    if formato == "es_AR":
        # 1.234,56 → 1234.56
        v = v.replace(".", "").replace(",", ".")
    else:
        v = v.replace(",", "")
    try:
        return Decimal(v)
    except Exception:
        return None


def parsear_csv(
    contenido: bytes,
    cliente_id: int = 0,
    delimitador: str = ";",
    formato_numero: Literal["es_AR", "en_US"] = "es_AR",
    banco: str = "",
) -> list[MovimientoBancario]:
    texto = contenido.decode("utf-8-sig")
    reader = csv.reader(StringIO(texto), delimiter=delimitador)
    headers = next(reader)
    col = _detectar_columnas(headers)

    if "fecha" not in col:
        raise ValueError("No se encontró columna de fecha")

    movimientos = []
    seq = 0
    for row in reader:
        if not row or all(not c.strip() for c in row):
            continue
        fecha_str = row[col["fecha"]].strip()
        try:
            fecha = datetime.strptime(fecha_str, "%Y-%m-%d").date()
        except ValueError:
            try:
                fecha = datetime.strptime(fecha_str, "%d/%m/%Y").date()
            except ValueError:
                continue

        desc = row[col.get("descripcion", 1)].strip() if "descripcion" in col else ""

        monto = None
        tipo = "debito"

        if "debito" in col and col["debito"] < len(row):
            m = _parsear_monto(row[col["debito"]], formato_numero)
            if m and m > 0:
                monto = m
                tipo = "debito"

        if monto is None and "credito" in col and col["credito"] < len(row):
            m = _parsear_monto(row[col["credito"]], formato_numero)
            if m and m > 0:
                monto = m
                tipo = "credito"

        if monto is None:
            continue

        seq += 1
        movimientos.append(MovimientoBancario(
            id=seq, cliente_id=cliente_id, fecha=fecha,
            descripcion=desc, monto=monto, tipo=tipo, banco=banco,
        ))

    return movimientos
