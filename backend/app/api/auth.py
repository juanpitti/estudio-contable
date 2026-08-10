"""Endpoint de login — emite JWT con rol."""

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.auth import autenticar, crear_token
from app.database import get_db

router = APIRouter(prefix="/auth", tags=["auth"])


class LoginIn(BaseModel):
    username: str
    password: str


@router.post("/login")
def login(datos: LoginIn, db: Session = Depends(get_db)) -> dict:
    usuario = autenticar(datos.username, datos.password, db)
    if usuario is None:
        raise HTTPException(status_code=401, detail="Credenciales inválidas")
    return {
        "access_token": crear_token(usuario["sub"], usuario["rol"]),
        "token_type": "bearer",
    }
