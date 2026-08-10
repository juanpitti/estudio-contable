"""Modelos SQLAlchemy — mapeo ORM de las entidades del dominio."""

from datetime import datetime, timezone

from sqlalchemy import Date, DateTime, ForeignKey, Integer, Numeric, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class DBUsuario(Base):
    __tablename__ = "usuarios"

    username: Mapped[str] = mapped_column(String(50), primary_key=True)
    password_hash: Mapped[str] = mapped_column(String(200), nullable=False)
    rol: Mapped[str] = mapped_column(String(20), nullable=False)


class DBCliente(Base):
    __tablename__ = "clientes"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    cuit: Mapped[str] = mapped_column(String(20), unique=True, nullable=False, index=True)
    razon_social: Mapped[str] = mapped_column(String(200), nullable=False)
    condicion_iva: Mapped[str] = mapped_column(String(5), nullable=False)

    comprobantes: Mapped[list["DBComprobante"]] = relationship(
        back_populates="cliente", cascade="all, delete-orphan"
    )


class DBComprobante(Base):
    __tablename__ = "comprobantes"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    cliente_id: Mapped[int] = mapped_column(ForeignKey("clientes.id"), nullable=False, index=True)
    tipo: Mapped[str] = mapped_column(String(10), nullable=False)  # venta / compra
    fecha: Mapped[Date] = mapped_column(Date, nullable=False)
    confirmado_por: Mapped[str] = mapped_column(String(50), nullable=False)
    confirmado_en: Mapped[DateTime] = mapped_column(
        DateTime, default=lambda: datetime.now(timezone.utc)
    )

    cliente: Mapped[DBCliente] = relationship(back_populates="comprobantes")
    lineas: Mapped[list["DBLineaAlicuota"]] = relationship(
        back_populates="comprobante", cascade="all, delete-orphan"
    )


class DBLineaAlicuota(Base):
    __tablename__ = "lineas_alicuota"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    comprobante_id: Mapped[int] = mapped_column(ForeignKey("comprobantes.id"), nullable=False)
    alicuota: Mapped[Numeric] = mapped_column(Numeric(5, 4), nullable=False)
    neto: Mapped[Numeric] = mapped_column(Numeric(18, 2), nullable=False)
    iva: Mapped[Numeric] = mapped_column(Numeric(18, 2), nullable=False)

    comprobante: Mapped[DBComprobante] = relationship(back_populates="lineas")


class DBRevision(Base):
    __tablename__ = "revisiones"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    entidad_tipo: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    entidad_id: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    usuario: Mapped[str] = mapped_column(String(100), nullable=False)
    estado: Mapped[str] = mapped_column(String(20), nullable=False)  # revisado/aprobado/rechazado
    comentario: Mapped[str] = mapped_column(Text, default="")
    timestamp: Mapped[DateTime] = mapped_column(
        DateTime, default=lambda: datetime.now(timezone.utc)
    )
