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


class TasaErrorTemaResponse(BaseModel):
    """Fila de `GET /analytics/materias/{materia_id}/tasa-error-por-tema` (RF-17)."""

    unidad_tematica: str
    tema: str
    cantidad_respuestas: int
    cantidad_incorrectas: int
    tasa_error: float


class DesempenoComisionFilaResponse(BaseModel):
    """Fila de `GET /analytics/materias/{id}/comisiones/{id}/desempeno` (`US-ADJ-44`, RF-20)."""

    estudiante_id: UUID
    nombre: str
    porcentaje_aciertos_acumulado: float | None
    actividades_pendientes: int


class EvolucionTemporalPuntoResponse(BaseModel):
    """Punto de la serie individual de `GET .../evolucion-temporal` (`US-ADJ-45`, RF-21)."""

    actividad_id: UUID
    titulo_actividad: str
    finalizada_en: datetime
    porcentaje_acierto: int


class EvolucionTemporalComisionPuntoResponse(BaseModel):
    """Punto de la serie de comisión de `GET .../evolucion-temporal` (`US-ADJ-45`, RF-21)."""

    actividad_id: UUID
    titulo_actividad: str
    porcentaje_aciertos_promedio: float


class RankingPreguntaFalladaResponse(BaseModel):
    """Fila de `GET .../ranking-preguntas-falladas` (`US-ADJ-46`, RF-22)."""

    pregunta_id: UUID
    enunciado: str
    unidad_tematica: str
    tema: str
    cantidad_presentaciones: int
    cantidad_fallos: int
    tasa_error: float


class CompletitudFilaResponse(BaseModel):
    """Fila de detalle de `GET .../completitud`, un estudiante del roster (`US-ADJ-47`, RF-23)."""

    estudiante_id: UUID
    nombre: str
    estado: str


class CompletitudResumenResponse(BaseModel):
    """Conteo agregado por estado de `GET .../completitud` (`US-ADJ-47`, RF-23)."""

    finalizadas: int
    en_curso: int
    suspendidas: int
    sin_iniciar: int


class CompletitudPorActividadResponse(BaseModel):
    """Respuesta completa de `GET /analytics/actividades/{id}/completitud` (`US-ADJ-47`, RF-23)."""

    detalle: list[CompletitudFilaResponse]
    resumen: CompletitudResumenResponse
