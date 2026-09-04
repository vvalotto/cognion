"""Schemas Pydantic de response de la API del BC Analytics (`US-4.1.2`)."""

from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel


class EvaluacionDetalleResponse(BaseModel):
    """Fila de detalle de una `Evaluacion` finalizada del Estudiante."""

    evaluacion_id: UUID
    actividad_id: UUID
    finalizada_en: datetime
    cantidad_correctas: int
    cantidad_incorrectas: int


class ResumenDesempenoResponse(BaseModel):
    """Acumulado sobre todas las evaluaciones finalizadas devueltas en el detalle."""

    total_correctas: int
    total_incorrectas: int
    porcentaje_acierto: int
    cantidad_evaluaciones: int


class DesempenoEstudianteResponse(BaseModel):
    """Respuesta completa de `GET /analytics/materias/{materia_id}/mi-desempeno` (RF-15)."""

    evaluaciones: list[EvaluacionDetalleResponse]
    resumen: ResumenDesempenoResponse
