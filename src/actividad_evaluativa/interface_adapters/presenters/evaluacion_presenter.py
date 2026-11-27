"""Presenters de evaluaciones y revisión (`ADR-031`): entidades -> salidas de la API.

Los `dataclass` de salida tienen los mismos campos que los esquemas de `frameworks/api/schemas.py`;
FastAPI los valida contra el `response_model` sin código extra. Sin Pydantic ni FastAPI.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Any
from uuid import UUID

from src.actividad_evaluativa.entities.evaluacion import Evaluacion, Respuesta
from src.actividad_evaluativa.entities.ports.pregunta_consulta_port import ContenidoPregunta
from src.actividad_evaluativa.entities.revision_evaluacion import RevisionEvaluacion


@dataclass(frozen=True)
class PreguntaAsignadaSalida:
    """Una pregunta del set del Estudiante, con su enunciado y opciones (sin la correcta)."""

    pregunta_id: UUID
    orden: int
    enunciado: str
    opciones: list[str] | None


@dataclass(frozen=True)
class RespuestaConfirmadaSalida:
    """El contenido de la respuesta vigente de una pregunta ya respondida."""

    pregunta_id: UUID
    contenido: dict[str, Any]


@dataclass(frozen=True)
class EvaluacionSalida:
    """Una evaluación del Estudiante."""

    id: UUID
    actividad_id: UUID
    estudiante_id: UUID
    preguntas_asignadas: list[PreguntaAsignadaSalida]
    preguntas_respondidas: list[UUID]
    respuestas_confirmadas: list[RespuestaConfirmadaSalida]
    estado: str
    iniciada_en: datetime


@dataclass(frozen=True)
class RespuestaSalida:
    """El resultado de registrar una respuesta (sin `es_correcta`)."""

    id: UUID
    pregunta_id: UUID
    numero_intento: int
    confirmada_en: datetime


@dataclass(frozen=True)
class DetallePreguntaRevisionSalida:
    """Una fila de la revisión de una evaluación."""

    pregunta_id: UUID
    orden: int
    texto: str
    respondida: bool
    contenido_propio: dict[str, Any] | None
    es_correcta: bool
    contenido_correcto: dict[str, Any] | None
    opciones: list[str] | None


@dataclass(frozen=True)
class RevisionEvaluacionSalida:
    """La revisión completa de una evaluación finalizada."""

    evaluacion_id: UUID
    cantidad_preguntas: int
    cantidad_correctas: int
    cantidad_incorrectas: int
    detalle: list[DetallePreguntaRevisionSalida]


def presentar_evaluacion(
    evaluacion: Evaluacion, contenidos: dict[UUID, ContenidoPregunta]
) -> EvaluacionSalida:
    """Arma la salida de una evaluación.

    `contenidos` trae el enunciado y las opciones de cada pregunta asignada (`US-3.4.6`, sin la
    respuesta correcta). `preguntas_respondidas` son los ids únicos, sin importar los intentos, y
    `respuestas_confirmadas` el contenido de la respuesta vigente de cada una (`US-ADJ-12`).
    """
    preguntas_respondidas = list(dict.fromkeys(r.pregunta_id for r in evaluacion.respuestas))
    respuestas_confirmadas = []
    for pregunta_id in preguntas_respondidas:
        vigente = evaluacion.respuesta_vigente_de(pregunta_id)
        if vigente is not None:
            respuestas_confirmadas.append(
                RespuestaConfirmadaSalida(pregunta_id=pregunta_id, contenido=vigente.contenido)
            )
    return EvaluacionSalida(
        id=evaluacion.id,
        actividad_id=evaluacion.actividad_id,
        estudiante_id=evaluacion.estudiante_id,
        preguntas_asignadas=[
            PreguntaAsignadaSalida(
                pregunta_id=p.pregunta_id,
                orden=p.orden,
                enunciado=contenidos[p.pregunta_id].texto,
                opciones=contenidos[p.pregunta_id].opciones,
            )
            for p in evaluacion.preguntas_asignadas
        ],
        preguntas_respondidas=preguntas_respondidas,
        respuestas_confirmadas=respuestas_confirmadas,
        estado=evaluacion.estado.value,
        iniciada_en=evaluacion.iniciada_en,
    )


def presentar_respuesta(respuesta: Respuesta) -> RespuestaSalida:
    """Arma la salida de una respuesta registrada."""
    return RespuestaSalida(
        id=respuesta.id,
        pregunta_id=respuesta.pregunta_id,
        numero_intento=respuesta.numero_intento,
        confirmada_en=respuesta.confirmada_en,
    )


def presentar_revision(revision: RevisionEvaluacion) -> RevisionEvaluacionSalida:
    """Arma la salida de la revisión de una evaluación."""
    return RevisionEvaluacionSalida(
        evaluacion_id=revision.evaluacion_id,
        cantidad_preguntas=revision.cantidad_preguntas,
        cantidad_correctas=revision.cantidad_correctas,
        cantidad_incorrectas=revision.cantidad_incorrectas,
        detalle=[
            DetallePreguntaRevisionSalida(
                pregunta_id=f.pregunta_id,
                orden=f.orden,
                texto=f.texto,
                respondida=f.respondida,
                contenido_propio=f.contenido_propio,
                es_correcta=f.es_correcta,
                contenido_correcto=f.contenido_correcto,
                opciones=f.opciones,
            )
            for f in revision.detalle
        ],
    )
