"""Modelos ORM (SQLAlchemy) del BC Identidad."""

from __future__ import annotations

import uuid

from sqlalchemy import Column, ForeignKey, String, Table
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.shared.frameworks.db import Base

comision_docentes = Table(
    "comision_docentes",
    Base.metadata,
    Column("comision_id", PGUUID(as_uuid=True), ForeignKey("comision.id"), primary_key=True),
    Column("docente_id", PGUUID(as_uuid=True), ForeignKey("docente.id"), primary_key=True),
)


class UsuarioModel(Base):
    """Fila de la tabla `usuario`."""

    __tablename__ = "usuario"

    id: Mapped[uuid.UUID] = mapped_column(
        PGUUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    nombre: Mapped[str] = mapped_column(String(200), nullable=False)
    email: Mapped[str] = mapped_column(String(255), nullable=False, unique=True)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)


class AdministradorModel(Base):
    """Fila de la tabla `administrador`, marca de perfil sobre `usuario`."""

    __tablename__ = "administrador"

    id: Mapped[uuid.UUID] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("usuario.id"), primary_key=True
    )


class DocenteModel(Base):
    """Fila de la tabla `docente`, marca de perfil sobre `usuario`."""

    __tablename__ = "docente"

    id: Mapped[uuid.UUID] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("usuario.id"), primary_key=True
    )


class EstudianteModel(Base):
    """Fila de la tabla `estudiante`, marca de perfil sobre `usuario`."""

    __tablename__ = "estudiante"

    id: Mapped[uuid.UUID] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("usuario.id"), primary_key=True
    )


class ComisionModel(Base):
    """Fila de la tabla `comision`, con sus docentes asignados vía `comision_docentes`."""

    __tablename__ = "comision"

    id: Mapped[uuid.UUID] = mapped_column(
        PGUUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    materia: Mapped[str] = mapped_column(String(200), nullable=False)
    horario: Mapped[str] = mapped_column(String(200), nullable=False)
    administrador_id: Mapped[uuid.UUID] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("administrador.id"), nullable=False
    )
    docentes: Mapped[list[DocenteModel]] = relationship(secondary=comision_docentes)
