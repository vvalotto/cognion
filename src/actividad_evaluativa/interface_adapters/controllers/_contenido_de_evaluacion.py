"""Enriquecimiento de una evaluación con el contenido de sus preguntas (`US-3.4.6`, `US-12.2.4`)."""

from __future__ import annotations

from uuid import UUID

from src.actividad_evaluativa.entities.evaluacion import Evaluacion
from src.actividad_evaluativa.entities.ports.pregunta_consulta_port import (
    ContenidoPregunta,
    PreguntaConsultaPort,
)


async def contenidos_de(
    evaluacion: Evaluacion, pregunta_consulta: PreguntaConsultaPort
) -> dict[UUID, ContenidoPregunta]:
    """Trae el enunciado y las opciones (sin la correcta) de cada pregunta asignada."""
    contenidos: dict[UUID, ContenidoPregunta] = {}
    for asignada in evaluacion.preguntas_asignadas:
        contenidos[asignada.pregunta_id] = await pregunta_consulta.obtener_contenido(
            asignada.pregunta_id
        )
    return contenidos
