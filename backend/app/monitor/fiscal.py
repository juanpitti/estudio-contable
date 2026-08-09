"""Monitor fiscal — alertas automáticas basadas en datos del sistema."""

from dataclasses import dataclass
from decimal import Decimal

from app.bitacora.modelo import obtener_ultima_revision
from app.calendario.vencimientos import alertas_vencimientos_proximos
from app.monotributo.categoria import alerta_proximidad_techo


@dataclass(frozen=True)
class AlertaMonitor:
    nivel: str  # info, warning, critical
    codigo: str
    mensaje: str
    cliente_id: int | None = None
    accion_sugerida: str = ""


def monitor_cliente(cliente_id: int, ingresos_acumulados: Decimal, categoria_monotributo: str) -> list[AlertaMonitor]:
    """Genera alertas para un cliente específico."""
    alertas = []

    # Alerta: monotributo cerca del techo
    alerta_mono = alerta_proximidad_techo(ingresos_acumulados, categoria_monotributo)
    if alerta_mono:
        alertas.append(AlertaMonitor(
            nivel=alerta_mono["nivel"],
            codigo=alerta_mono["codigo"],
            mensaje=alerta_mono["mensaje"],
            cliente_id=cliente_id,
            accion_sugerida="Recategorizar en ARCA antes del vencimiento",
        ))

    # Alerta: IVA sin revisar
    ultima = obtener_ultima_revision("liquidacion_iva", cliente_id)
    if not ultima or ultima.estado != "aprobado":
        alertas.append(AlertaMonitor(
            nivel="warning",
            codigo="IVA_SIN_REVISAR",
            mensaje="La liquidación de IVA no fue aprobada",
            cliente_id=cliente_id,
            accion_sugerida="Revisar y aprobar la liquidación del período",
        ))

    return alertas


def monitor_global(clientes: list[dict]) -> list[AlertaMonitor]:
    """Genera alertas globales para todo el estudio."""
    alertas = []

    # Vencimientos próximos
    venc_alertas = alertas_vencimientos_proximos(dias_ventana=7)
    for va in venc_alertas:
        alertas.append(AlertaMonitor(
            nivel=va["nivel"],
            codigo=f"VENCIMIENTO_{va['impuesto'].upper().replace(' ', '_')}",
            mensaje=va["mensaje"],
            accion_sugerida="Presentar declaración antes del vencimiento",
        ))

    # Clientes con alertas individuales
    for c in clientes:
        alertas_cliente = monitor_cliente(
            cliente_id=c["id"],
            ingresos_acumulados=Decimal(str(c.get("ingresos_acumulados", "0"))),
            categoria_monotributo=c.get("categoria_monotributo", "A"),
        )
        alertas.extend(alertas_cliente)

    return alertas


def resumen_estudio(clientes: list[dict]) -> dict:
    """Resumen ejecutivo del estado del estudio."""
    total = len(clientes)
    alertas = monitor_global(clientes)
    criticas = sum(1 for a in alertas if a.nivel == "critical")
    warnings = sum(1 for a in alertas if a.nivel == "warning")

    return {
        "total_clientes": total,
        "alertas_activas": len(alertas),
        "alertas_critical": criticas,
        "alertas_warning": warnings,
        "clientes_al_dia": max(0, total - len(set(a.cliente_id for a in alertas if a.cliente_id))),
    }
