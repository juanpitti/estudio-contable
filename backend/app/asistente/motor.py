"""Asistente IA — responde preguntas sobre datos propios del estudio.

Blindaje legal: nunca asesora normativamente. Solo citan datos del sistema.
"""

import re
from dataclasses import dataclass


@dataclass(frozen=True)
class RespuestaAsistente:
    texto: str
    fuente: str  # Qué dato del sistema se consultó
    links: list[dict] = ()  # Links a pantallas relevantes


_INTENCIONES = [
    {
        "keywords": ["iva sin revisar", "sin revisar", "iva pendiente", "aprobar iva"],
        "intencion": "iva_sin_revisar",
    },
    {
        "keywords": ["monotributo cerca techo", "cerca del techo", "recategorizar", "techo monotributo"],
        "intencion": "monotributo_techo",
    },
    {
        "keywords": ["vencimiento", "vence", "vencimientos proximos", "que vence"],
        "intencion": "vencimientos",
    },
    {
        "keywords": ["cuantos clientes", "total clientes", "cantidad clientes", "cuantos tengo"],
        "intencion": "total_clientes",
    },
    {
        "keywords": ["alertas", "que alertas", "hay alertas", "problemas"],
        "intencion": "alertas",
    },
]


def _detectar_intencion(pregunta: str) -> str | None:
    import unicodedata
    pregunta_lower = unicodedata.normalize("NFKD", pregunta).encode("ASCII", "ignore").decode("ASCII").lower()
    for item in _INTENCIONES:
        for kw in item["keywords"]:
            if kw in pregunta_lower:
                return item["intencion"]
    return None
    pregunta_lower = pregunta.lower()
    for item in _INTENCIONES:
        for kw in item["keywords"]:
            if kw in pregunta_lower:
                return item["intencion"]
    return None


def responder(
    pregunta: str,
    clientes: list[dict],
    alertas: list[dict],
    vencimientos: list[dict],
) -> RespuestaAsistente:
    """Procesa una pregunta y responde con datos del sistema."""
    intencion = _detectar_intencion(pregunta)

    if intencion == "iva_sin_revisar":
        # Clientes sin revisión aprobada
        sin_revisar = [c for c in clientes if c.get("semaforo") != "verde"]
        if not sin_revisar:
            return RespuestaAsistente(
                texto="Todos los clientes tienen la IVA revisada y aprobada.",
                fuente="bitácora de revisiones",
            )
        nombres = ", ".join([c["razon_social"] for c in sin_revisar[:5]])
        mas = f" y {len(sin_revisar) - 5} más" if len(sin_revisar) > 5 else ""
        return RespuestaAsistente(
            texto=f"Clientes con IVA sin revisar: {nombres}{mas}.",
            fuente="bitácora de revisiones",
            links=[{"label": "Ver Dashboard", "path": "/dashboard"}],
        )

    if intencion == "monotributo_techo":
        # Clientes con alerta de monotributo
        alertas_mono = [a for a in alertas if "MONOTRIBUTO" in a.get("codigo", "")]
        if not alertas_mono:
            return RespuestaAsistente(
                texto="Ningún cliente está cerca del techo de monotributo.",
                fuente="cálculo de categorías AFIP",
            )
        nombres = ", ".join([f"Cliente {a.get('cliente_id')}" for a in alertas_mono[:5]])
        return RespuestaAsistente(
            texto=f"Clientes cerca del techo: {nombres}.",
            fuente="cálculo de categorías AFIP",
            links=[{"label": "Ver Monotributo", "path": "/monotributo"}],
        )

    if intencion == "vencimientos":
        if not vencimientos:
            return RespuestaAsistente(
                texto="No hay vencimientos en los próximos 7 días.",
                fuente="calendario fiscal",
            )
        lista = "; ".join([f"{v['impuesto']} ({v['fecha']})" for v in vencimientos[:5]])
        return RespuestaAsistente(
            texto=f"Próximos vencimientos: {lista}.",
            fuente="calendario fiscal",
            links=[{"label": "Ver Dashboard", "path": "/dashboard"}],
        )

    if intencion == "total_clientes":
        return RespuestaAsistente(
            texto=f"Tenés {len(clientes)} cliente{'s' if len(clientes) != 1 else ''} en la cartera.",
            fuente="base de clientes",
        )

    if intencion == "alertas":
        criticas = sum(1 for a in alertas if a.get("nivel") == "critical")
        warnings = sum(1 for a in alertas if a.get("nivel") == "warning")
        return RespuestaAsistente(
            texto=f"Hay {len(alertas)} alertas activas: {criticas} críticas y {warnings} warnings.",
            fuente="monitor fiscal",
            links=[{"label": "Ver Dashboard", "path": "/dashboard"}],
        )

    return RespuestaAsistente(
        texto="No entendí la pregunta. Probá con: '¿qué clientes tienen la IVA sin revisar?' o '¿cuáles son los vencimientos próximos?'",
        fuente="sistema de ayuda",
    )
