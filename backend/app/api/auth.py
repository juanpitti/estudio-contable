"""Endpoint de login — emite JWT con rol."""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.auth import autenticar, crear_token

router = APIRouter(prefix="/auth", tags=["auth"])


class LoginIn(BaseModel):
    username: str
    password: str


@router.post("/login")
def login(datos: LoginIn) -> dict:
    usuario = autenticar(datos.username, datos.password)
    if usuario is None:
        raise HTTPException(status_code=401, detail="Credenciales inválidas")
    return {
        "access_token": crear_token(usuario["sub"], usuario["rol"]),
        "token_type": "bearer",
    }
