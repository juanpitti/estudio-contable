"""API de generación de F.931."""

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from app.api.clientes import RepoClientes, get_repo
from app.auth import requerir_rol
from app.f931.generador import generar_txt_f931

router = APIRouter(tags=["f931"])


class EmpleadoIn(BaseModel):
    cuit: str
    apellido_nombre: str
    remuneracion: str
    aportes: str
    contribuciones: str
    situacion_revista: str = "1"


class F931In(BaseModel):
    periodo: str
    empleados: list[EmpleadoIn]


@router.post("/clientes/{cliente_id}/f931/generar")
def generar_f931(
    cliente_id: int,
    datos: F931In,
    repo: RepoClientes = Depends(get_repo),
    usuario: dict = Depends(requerir_rol("owner", "senior")),
):
    cliente = repo.obtener(cliente_id)
    if cliente is None:
        raise HTTPException(status_code=404, detail="Cliente no encontrado")

    txt = generar_txt_f931(
        cuit_empleador=cliente.cuit.replace("-", ""),
        periodo=datos.periodo,
        empleados=[e.model_dump() for e in datos.empleados],
    )

    return {"txt": txt, "nombre_archivo": f"F931_{cliente.cuit}_{datos.periodo}.txt"}
