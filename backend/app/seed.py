"""Seed de datos iniciales — usuarios por defecto del estudio.

Idempotente: solo inserta si no existen.
"""

from sqlalchemy.orm import Session

from app.auth import hash_password
from app.database import SessionLocal
from app.models_db import DBUsuario


USUARIOS_SEED = [
    {"username": "owner", "password": "owner123", "rol": "owner"},
    {"username": "senior", "password": "senior123", "rol": "senior"},
]


def seed_usuarios_en_db(db: Session) -> None:
    existentes = {u.username for u in db.query(DBUsuario).all()}
    for u in USUARIOS_SEED:
        if u["username"] not in existentes:
            db.add(DBUsuario(
                username=u["username"],
                password_hash=hash_password(u["password"]),
                rol=u["rol"],
            ))
    db.commit()


def seed_usuarios() -> None:
    db = SessionLocal()
    try:
        seed_usuarios_en_db(db)
    finally:
        db.close()
