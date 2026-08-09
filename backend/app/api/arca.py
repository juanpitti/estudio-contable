"""API de descarga de comprobantes desde ARCA (wsfe).

Stub inicial: la arquitectura está lista pero requiere certificado de
homologación/producción del cliente para funcionar end-to-end.
"""

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from app.api.clientes import RepoClientes, get_repo
from app.api.comprobantes import RepoComprobantes, get_repo_comprobantes
from app.auth import requerir_rol

router = APIRouter(tags=["arca"])


class DescargaArcaIn(BaseModel):
    cert_path: str
    key_path: str
    pto_vta: int


def _wsfe_consultar_comprobantes(cert_path: str, key_path: str, cuit: str, pto_vta: int):
    """Wrapper sobre wsfe para obtener últimos comprobantes autorizados.
    
    Por ahora: requiere certificado real. Cuando esté disponible,
    descomentar e integrar con app.arca.wsfe.
    """
    raise NotImplementedError(
        "Descarga ARCA requiere certificado de homologación del cliente. "
        "Verificar docs/etapa0/verificacion-rg-74-2022.md"
    )


@router.post("/clientes/{cliente_id}/arca/descargar", status_code=201)
def descargar_comprobantes_arca(
    cliente_id: int,
    datos: DescargaArcaIn,
    repo: RepoComprobantes = Depends(get_repo_comprobantes),
    repo_cli: RepoClientes = Depends(get_repo),
    usuario: dict = Depends(requerir_rol("owner", "senior")),
):
    cliente = repo_cli.obtener(cliente_id)
    if cliente is None:
        raise HTTPException(status_code=404, detail="Cliente no encontrado")

    try:
        raw = _wsfe_consultar_comprobantes(
            datos.cert_path, datos.key_path, cliente.cuit, datos.pto_vta
        )
    except NotImplementedError as e:
        raise HTTPException(status_code=501, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"Error ARCA: {e}")

    return {
        "descargados": 0,
        "pendientes_confirmacion": 0,
        "mensaje": "Stub: la descarga ARCA requiere certificado de homologación del cliente.",
    }
