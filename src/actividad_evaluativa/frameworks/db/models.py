"""Modelo ORM (SQLAlchemy) de la tabla `events` — event store del BC Actividad Evaluativa.

Tabla única compartida por todos los aggregates del BC (`ActividadEvaluativaPeriodoAbierto`,
`Evaluacion`, y los que se agreguen después) — el stream de cada uno se aísla por
`(aggregate_type, aggregate_id)` (`BC-actividad-evaluativa-modelo.md` §6).
"""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any

from sqlalchemy import DateTime, Integer, String, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column

from src.shared.frameworks.db import Base


class EventoModel(Base):
    """Fila de la tabla `events` — un evento de dominio ya persistido de un stream.

    El índice único `(aggregate_type, aggregate_id, sequence_number)` sostiene tanto el
    replay ordenado como la detección de concurrencia optimista: un segundo `append` con el
    mismo `sequence_number` para el mismo stream viola la constraint antes de que
    `SQLAlchemyEventStore` necesite compararlo en memoria.
    """

    __tablename__ = "events"
    __table_args__ = (
        UniqueConstraint(
            "aggregate_type",
            "aggregate_id",
            "sequence_number",
            name="uq_events_stream_sequence",
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        PGUUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    aggregate_type: Mapped[str] = mapped_column(String(100), nullable=False)
    aggregate_id: Mapped[uuid.UUID] = mapped_column(PGUUID(as_uuid=True), nullable=False)
    sequence_number: Mapped[int] = mapped_column(Integer, nullable=False)
    event_type: Mapped[str] = mapped_column(String(100), nullable=False)
    payload: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False)
    occurred_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)


class RankingPorSesionModel(Base):
    """Read model `ranking_por_sesion` — puntaje acumulado por participante (`US-6.2.3`)."""

    __tablename__ = "ranking_por_sesion"

    sesion_id: Mapped[uuid.UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True)
    estudiante_id: Mapped[uuid.UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True)
    puntaje_acumulado: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    ultima_actualizacion: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)


class DistribucionPorPreguntaModel(Base):
    """Read model `distribucion_por_pregunta` — respuestas por opción (`US-6.2.3`)."""

    __tablename__ = "distribucion_por_pregunta"

    sesion_id: Mapped[uuid.UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True)
    pregunta_id: Mapped[uuid.UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True)
    opcion: Mapped[str] = mapped_column(String(50), primary_key=True)
    cantidad: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
