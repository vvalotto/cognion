"""Modelos ORM (SQLAlchemy) del BC Banco de Preguntas."""

from __future__ import annotations

import uuid

from sqlalchemy import ForeignKey, String
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column

from src.shared.frameworks.db import Base


class MateriaModel(Base):
    """Fila de la tabla `materia`, con `nombre` único (INV-BP-00)."""

    __tablename__ = "materia"

    id: Mapped[uuid.UUID] = mapped_column(
        PGUUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    nombre: Mapped[str] = mapped_column(String(200), nullable=False, unique=True)


class BancoModel(Base):
    """Fila de la tabla `banco`, con `materia_id` único (INV-BP-01: a lo sumo un banco/materia)."""

    __tablename__ = "banco"

    id: Mapped[uuid.UUID] = mapped_column(
        PGUUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    materia_id: Mapped[uuid.UUID] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("materia.id"), nullable=False, unique=True
    )
