from dataclasses import dataclass
from decimal import Decimal

from app.iva.calculadora import LiquidacionIva


@dataclass(frozen=True)
class AlertaIva:
    nivel: str  # "info" | "warning" | "critical"
    codigo: str
    mensaje: str


def analizar_alertas(
    liq: LiquidacionIva,
    historial_saldos_favor: list[Decimal],
) -> list[AlertaIva]:
    alertas: list[AlertaIva] = []
    total_debito = liq.total_debito
    total_credito = liq.total_credito

    # Alerta: salto de crédito fiscal
    if total_credito > total_debito and total_debito > 0:
        ratio = total_credito / total_debito
        if ratio > Decimal("2"):
            alertas.append(AlertaIva(
                nivel="critical",
                codigo="salto_credito_fiscal",
                mensaje=f"El crédito fiscal ({total_credito}) supera el doble del débito ({total_debito}). Revisar compras.",
            ))
        elif ratio > Decimal("1.5"):
            alertas.append(AlertaIva(
                nivel="warning",
                codigo="salto_credito_fiscal",
                mensaje=f"El crédito fiscal ({total_credito}) supera el débito ({total_debito}) en más del 50%. Verificar.",
            ))

    # Alerta: IVA técnico acumulado (3+ períodos con saldo a favor)
    if liq.saldo_a_favor_final > 0:
        consecutivos = 1  # período actual
        for s in reversed(historial_saldos_favor):
            if s > 0:
                consecutivos += 1
            else:
                break
        if consecutivos >= 3:
            alertas.append(AlertaIva(
                nivel="warning",
                codigo="iva_tecnico_acumulado",
                mensaje=f"IVA técnico acumulado por {consecutivos} períodos consecutivos. Saldo a favor actual: {liq.saldo_a_favor_final}.",
            ))

    # Info: uso parcial de saldo a favor anterior
    if liq.saldo_favor_anterior > 0 and liq.saldo_a_pagar > 0:
        alertas.append(AlertaIva(
            nivel="info",
            codigo="saldo_favor_parcial",
            mensaje=f"Se utilizó parcialmente el saldo a favor anterior ({liq.saldo_favor_anterior}). A pagar: {liq.saldo_a_pagar}.",
        ))

    return alertas
