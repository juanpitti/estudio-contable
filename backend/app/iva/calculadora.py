"""Calculadora de pre-liquidación de IVA (Plan 4 / Etapa 2).

Reglas:
- Débito fiscal = Σ IVA de ventas; Crédito fiscal = Σ IVA de compras.
- Si débito − crédito > 0: saldo a pagar (se descuenta saldo a favor anterior).
- Si crédito > débito: IVA técnico → saldo a favor del contribuyente (arrastre).
- El saldo a favor nunca queda negativo: se arrastra al período siguiente.

Dinero con Decimal, siempre.
"""

from dataclasses import dataclass
from decimal import Decimal

from app.iva.comprobante import ComprobanteIva


@dataclass(frozen=True)
class LiquidacionIva:
    debito: dict[Decimal, Decimal]
    credito: dict[Decimal, Decimal]
    saldo_favor_anterior: Decimal
    saldo_a_pagar: Decimal
    saldo_a_favor_final: Decimal

    @property
    def total_debito(self) -> Decimal:
        return sum(self.debito.values(), Decimal("0"))

    @property
    def total_credito(self) -> Decimal:
        return sum(self.credito.values(), Decimal("0"))


def _acumular(comprobantes: list[ComprobanteIva]) -> dict[Decimal, Decimal]:
    totales: dict[Decimal, Decimal] = {}
    for comp in comprobantes:
        for linea in comp.lineas:
            totales[linea.alicuota] = totales.get(linea.alicuota, Decimal("0")) + linea.iva
    return totales


def liquidacion_iva(
    ventas: list[ComprobanteIva],
    compras: list[ComprobanteIva],
    saldo_favor_anterior: Decimal,
) -> LiquidacionIva:
    debito = _acumular(ventas)
    credito = _acumular(compras)

    resultado = sum(debito.values(), Decimal("0")) - sum(credito.values(), Decimal("0"))
    neto = resultado - saldo_favor_anterior

    if neto > 0:
        a_pagar, a_favor = neto, Decimal("0")
    else:
        a_pagar, a_favor = Decimal("0"), -neto

    return LiquidacionIva(
        debito=debito,
        credito=credito,
        saldo_favor_anterior=saldo_favor_anterior,
        saldo_a_pagar=a_pagar,
        saldo_a_favor_final=a_favor,
    )
