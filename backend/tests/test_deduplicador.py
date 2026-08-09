from decimal import Decimal
from datetime import date

from app.conciliacion.movimiento import MovimientoBancario
from app.conciliacion.deduplicador import deduplicar


def test_sin_duplicados():
    movs = [
        MovimientoBancario(1, 1, date(2026, 8, 1), "PAGO A", Decimal("1000"), "debito"),
        MovimientoBancario(2, 1, date(2026, 8, 2), "PAGO B", Decimal("2000"), "debito"),
    ]
    unicos, dups = deduplicar(movs)
    assert len(unicos) == 2
    assert len(dups) == 0


def test_detecta_duplicado_exacto():
    movs = [
        MovimientoBancario(1, 1, date(2026, 8, 1), "PAGO", Decimal("1000"), "debito"),
        MovimientoBancario(2, 1, date(2026, 8, 1), "PAGO", Decimal("1000"), "debito"),
    ]
    unicos, dups = deduplicar(movs)
    assert len(unicos) == 1
    assert len(dups) == 1


def test_diferente_monto_no_es_duplicado():
    movs = [
        MovimientoBancario(1, 1, date(2026, 8, 1), "PAGO", Decimal("1000"), "debito"),
        MovimientoBancario(2, 1, date(2026, 8, 1), "PAGO", Decimal("2000"), "debito"),
    ]
    unicos, dups = deduplicar(movs)
    assert len(unicos) == 2
    assert len(dups) == 0
