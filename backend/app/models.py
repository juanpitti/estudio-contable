"""Modelos de dominio — cartera de clientes del estudio."""

from typing import Literal

from pydantic import BaseModel, field_validator

from app.cuit import formatear_cuit

CondicionIva = Literal["RI", "MT", "EX", "CF"]  # Resp. Inscripto, Monotributo, Exento, Consumidor Final


class ClienteIn(BaseModel):
    cuit: str
    razon_social: str
    condicion_iva: CondicionIva

    @field_validator("cuit")
    @classmethod
    def _cuit_valido(cls, v: str) -> str:
        # Normaliza a XX-XXXXXXXX-X; lanza ValueError (-> 422) si es inválido
        return formatear_cuit(v)

    @field_validator("razon_social")
    @classmethod
    def _razon_social_no_vacia(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValueError("razon_social no puede estar vacía")
        return v


class Cliente(ClienteIn):
    id: int
