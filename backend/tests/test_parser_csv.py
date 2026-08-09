from decimal import Decimal
from datetime import date

from app.conciliacion.movimiento import MovimientoBancario
from app.conciliacion.parser_csv import parsear_csv


def test_parsear_csv_simple():
    csv = b"fecha;descripcion;debito;\n2026-08-01;PAGO PROVEEDOR;15000,50;\n"
    movs = parsear_csv(csv, delimitador=";", formato_numero="es_AR")
    assert len(movs) == 1
    assert movs[0].fecha == date(2026, 8, 1)
    assert movs[0].descripcion == "PAGO PROVEEDOR"
    assert movs[0].monto == Decimal("15000.50")
    assert movs[0].tipo == "debito"


def test_parsear_csv_coma_decimal():
    csv = b"fecha,descripcion,credito,\n2026-08-02,COBRO CLIENTE,25000.00,\n"
    movs = parsear_csv(csv, delimitador=",", formato_numero="en_US")
    assert len(movs) == 1
    assert movs[0].monto == Decimal("25000.00")
    assert movs[0].tipo == "credito"


def test_parsear_csv_ignora_saldo():
    csv = b"fecha;concepto;debito;credito;saldo;\n2026-08-03;FACTURA;5000;;10000;\n"
    movs = parsear_csv(csv, delimitador=";", formato_numero="es_AR")
    assert len(movs) == 1
    assert movs[0].monto == Decimal("5000")


def test_parsear_csv_detecta_columnas():
    csv = "Fecha;Descripcion;Importe Debido;Importe Acreditado;\n2026-08-04;PAGO;10000;;\n2026-08-05;COBRO;;20000;\n".encode("utf-8")
    movs = parsear_csv(csv, delimitador=";", formato_numero="es_AR")
    assert len(movs) == 2
    assert movs[0].monto == Decimal("10000")
    assert movs[0].tipo == "debito"
    assert movs[1].monto == Decimal("20000")
    assert movs[1].tipo == "credito"
