# Verificación normativa — "RG/DIG ARCA 74/2022" (Etapa 0)

> **Estado: NO VERIFICADA — 2026-08-08.** No asumir su contenido hasta completar el checklist.
> El Plan v4 exige esta verificación escrita antes de construir descargadores (Etapa 2).

## Qué afirma el Plan v4

> "Verificación escrita de RG/DIG ARCA 74/2022 — qué canal de extracción está permitido"
> (contexto: SOS tiene Autoimpo suspendido por esa norma).

## Qué se verificó hasta ahora

| Fecha | Fuente | Resultado |
|---|---|---|
| 2026-08-08 | Búsqueda web + Biblioteca Electrónica ARCA (biblioteca.afip.gob.ar) | **No aparece una RG 74/2022 ni DIG 74/2022** con ese número y tema. Puede ser una Disposición (DI) interna, un número impreciso, o referencia de segunda mano del benchmark competitivo. |
| 2026-08-08 | RG 5198/2022 y RG 5824/2026 (halladas en la búsqueda) | Normas de emisión de comprobantes; no regulan extracción/descarga de datos. La RG 5824/2026 (vigente para operaciones desde 2026-07-01) sí afecta la Etapa 4 (emisión/CAE). |

## Checklist de verificación manual (owner o contador)

- [ ] Buscar en Biblioteca Electrónica ARCA: "74/2022" filtrando por tipo Disposición (DI), Disposición DIG y Resolución General.
- [ ] Consultar el servicio "Comprobantes electrónicos — consulta/descarga por terceros" y sus Términos y Condiciones vigentes.
- [ ] Confirmar si la extracción vía WS (wsfe / ws_sr_constancia / padrón) con certificado del cliente es canal expresamente permitido para software de terceros.
- [ ] Documentar por escrito: canal permitido, canal prohibido, y fundamento (norma + artículo).
- [ ] Cruzar con el caso SOS/Autoimpo: pedir al contacto del benchmark la norma exacta que citó.

## Regla operativa mientras tanto

Todo descargador del proyecto usa **únicamente WS oficiales con certificado del cliente**
(WSAA + wsfe), el canal ya implementado y testeado en `app/arca/`. Ningún scraping de
portales con clave fiscal del cliente hasta que esta verificación quede en VERIFICADA.

## Próxima revisión

Antes de iniciar Etapa 2 (Semana 5). Responsable: owner.
