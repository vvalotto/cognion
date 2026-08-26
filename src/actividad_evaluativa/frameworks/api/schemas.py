"""Schemas Pydantic de request/response de la API del BC Actividad Evaluativa."""

from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field


class CrearActividadRequest(BaseModel):
    """Body de la request de alta de actividad de período abierto."""

    materia_id: UUID
    fecha_apertura: datetime
    fecha_cierre: datetime
    cantidad_preguntas: int = Field(..., ge=1)
    cantidad_intentos_permitidos: int = Field(..., ge=1)


class ActividadResponse(BaseModel):
    """Representación de una `ActividadEvaluativaPeriodoAbierto` devuelta por la API."""

    id: UUID
    materia_id: UUID
    fecha_apertura: datetime
    fecha_cierre: datetime
    cantidad_preguntas: int
    cantidad_intentos_permitidos: int
    cerrada_manualmente: bool
