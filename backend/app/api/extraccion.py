"""Endpoint de extracción — pantalla "subir factura" de la Etapa 1.

Recibe PDF/foto/ticket, corre el pipeline Plan 1 y devuelve los campos
con confianza y fuente por dato (trazabilidad, Plan v4 regla 6).
"""

from dataclasses import asdict

from fastapi import APIRouter, Depends, UploadFile

from app.auth import usuario_actual
from app.extractor.pipeline import PipelineExtraccion

router = APIRouter(prefix="/extraccion", tags=["extraccion"])

_pipeline = PipelineExtraccion()


@router.post("/comprobante")
async def extraer_comprobante(
    archivo: UploadFile, _usuario: dict = Depends(usuario_actual)
) -> dict:
    resultado = _pipeline.procesar(await archivo.read())
    return {
        "estado": resultado.estado,
        "campos": {nombre: asdict(c) for nombre, c in resultado.campos.items()},
    }
