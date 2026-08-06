"""Modelos ORM (SQLAlchemy) del BC Banco de Preguntas."""

from __future__ import annotations

import uuid
from typing import Any

from sqlalchemy import Boolean, ForeignKey, String
from sqlalchemy.dialects.postgresql import JSONB
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


class PreguntaPlantillaModel(Base):
    """Fila de la tabla `pregunta_plantilla`, con `tipo` como columna discriminadora.

    `opciones` es `None` para preguntas verdadero/falso (`US-2.1.4`); esta US solo
    persiste el tipo `opcion_multiple`.
    """

    __tablename__ = "pregunta_plantilla"

    id: Mapped[uuid.UUID] = mapped_column(
        PGUUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    banco_id: Mapped[uuid.UUID] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("banco.id"), nullable=False
    )
    tipo: Mapped[str] = mapped_column(String(30), nullable=False)
    texto: Mapped[str] = mapped_column(String(2000), nullable=False)
    opciones: Mapped[list[dict[str, Any]] | None] = mapped_column(JSONB, nullable=True)
    unidad_tematica: Mapped[str] = mapped_column(String(200), nullable=False)
    tema: Mapped[str] = mapped_column(String(200), nullable=False)
    dificultad: Mapped[str] = mapped_column(String(10), nullable=False)
    importancia: Mapped[str] = mapped_column(String(10), nullable=False)
    activa: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
