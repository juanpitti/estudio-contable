"""Autenticación JWT con roles (Etapa 1: owner/senior).

Usuarios seed SOLO para desarrollo/staging ficticio. En producción: gestión
de usuarios por estudio (Plan 10) con DB real.
"""

import hashlib
import hmac
import os
import secrets
from datetime import datetime, timedelta, timezone

import jwt
from fastapi import Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

_SECRETO = os.environ.get("JWT_SECRET", "dev-secret-cambiar-en-produccion")
_ALGORITMO = "HS256"
_DURACION = timedelta(hours=8)
_esquema = HTTPBearer(auto_error=False)


def hash_password(password: str, salt: str | None = None) -> str:
    salt = salt or secrets.token_hex(16)
    digest = hashlib.pbkdf2_hmac("sha256", password.encode(), bytes.fromhex(salt), 100_000)
    return f"{salt}:{digest.hex()}"


def verificar_password(password: str, almacenado: str) -> bool:
    salt, digest = almacenado.split(":", 1)
    candidato = hashlib.pbkdf2_hmac("sha256", password.encode(), bytes.fromhex(salt), 100_000)
    return hmac.compare_digest(candidato.hex(), digest)


# Usuarios de desarrollo (datos ficticios, Plan v4 regla 2)
USUARIOS: dict[str, dict] = {
    "owner": {"password_hash": hash_password("owner123"), "rol": "owner"},
    "senior": {"password_hash": hash_password("senior123"), "rol": "senior"},
}


def autenticar(username: str, password: str) -> dict | None:
    usuario = USUARIOS.get(username)
    if usuario and verificar_password(password, usuario["password_hash"]):
        return {"sub": username, "rol": usuario["rol"]}
    return None


def crear_token(sub: str, rol: str) -> str:
    ahora = datetime.now(timezone.utc)
    return jwt.encode(
        {"sub": sub, "rol": rol, "iat": ahora, "exp": ahora + _DURACION},
        _SECRETO,
        algorithm=_ALGORITMO,
    )


def decodificar_token(token: str) -> dict:
    return jwt.decode(token, _SECRETO, algorithms=[_ALGORITMO])


def usuario_actual(
    credenciales: HTTPAuthorizationCredentials | None = Depends(_esquema),
) -> dict:
    if credenciales is None:
        raise HTTPException(status_code=401, detail="Token requerido")
    try:
        return decodificar_token(credenciales.credentials)
    except jwt.PyJWTError:
        raise HTTPException(status_code=401, detail="Token inválido o vencido")


def requerir_rol(*roles: str):
    def _verificar(usuario: dict = Depends(usuario_actual)) -> dict:
        if usuario["rol"] not in roles:
            raise HTTPException(status_code=403, detail="Rol insuficiente")
        return usuario

    return _verificar
