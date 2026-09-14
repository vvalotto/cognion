"""Caso de uso: ranking de preguntas más falladas de una materia (`US-ADJ-46`, RF-22)."""

from __future__ import annotations

from dataclasses import dataclass
from uuid import UUID

from src.analytics.entities.errors import ComisionNoPerteneceAMateria
from src.analytics.entities.ports.comision_consulta_port import ComisionConsultaPort
from src.analytics.entities.ports.evaluacion_desempeno_consulta_port import (
    EvaluacionDesempenoConsultaPort,
    RespuestaVigente,
)
from src.analytics.entities.ports.pregunta_metadato_consulta_port import (
    MetadatoPreguntaResumen,
    PreguntaMetadatoConsultaPort,
)


@dataclass(frozen=True)
class RankingPreguntaFallada:
    """Agregado de error de una pregunta puntual sobre las respuestas consultadas."""

    pregunta_id: UUID
    enunciado: str
    unidad_tematica: str
    tema: str
    cantidad_presentaciones: int
    cantidad_fallos: int
    tasa_error: float


class ObtenerRankingPreguntasFalladasUseCase:
    """Agrega respuestas vigentes por pregunta, acotando opcionalmente a una comisión (RF-22).

    Reusa exactamente la misma fuente que `ObtenerTasaErrorPorTemaUseCase` (`US-4.2.4`),
    cambiando la clave de agrupación de `(unidad_tematica, tema)` a `pregunta_id`.
    """

    def __init__(
        self,
        evaluacion_desempeno_consulta: EvaluacionDesempenoConsultaPort,
        comision_consulta: ComisionConsultaPort,
        pregunta_metadato_consulta: PreguntaMetadatoConsultaPort,
    ) -> None:
        """Recibe los 3 puertos de consulta que compone el agregado."""
        self._evaluacion_desempeno_consulta = evaluacion_desempeno_consulta
        self._comision_consulta = comision_consulta
        self._pregunta_metadato_consulta = pregunta_metadato_consulta

    async def execute(
        self, materia_id: UUID, comision_id: UUID | None
    ) -> list[RankingPreguntaFallada]:
        """Devuelve el ranking ordenado por `tasa_error` descendente.

        `comision_id` que no pertenece a `materia_id` → `raise ComisionNoPerteneceAMateria`.
        Sin `comision_id`, agrega toda la materia.
        """
        estudiante_ids = await self._resolver_estudiante_ids(materia_id, comision_id)
        respuestas = (
            await self._evaluacion_desempeno_consulta.listar_respuestas_vigentes_de_materia(
                materia_id, estudiante_ids
            )
        )
        if not respuestas:
            return []

        metadatos = await self._pregunta_metadato_consulta.obtener_metadatos(
            list({respuesta.pregunta_id for respuesta in respuestas})
        )
        return _ranking_ordenado(respuestas, metadatos)

    async def _resolver_estudiante_ids(
        self, materia_id: UUID, comision_id: UUID | None
    ) -> list[UUID] | None:
        """`None` si no se acota a comisión; lista de estudiantes de la comisión si sí."""
        if comision_id is None:
            return None
        comisiones = await self._comision_consulta.listar_comisiones_por_materia(materia_id)
        if comision_id not in {comision.id for comision in comisiones}:
            raise ComisionNoPerteneceAMateria(comision_id, materia_id)
        estudiantes = await self._comision_consulta.listar_estudiantes(comision_id)
        return [estudiante.id for estudiante in estudiantes]


def _ranking_ordenado(
    respuestas: list[RespuestaVigente], metadatos: dict[UUID, MetadatoPreguntaResumen]
) -> list[RankingPreguntaFallada]:
    """Agrupa por `pregunta_id`, calcula la tasa de error y ordena descendente.

    Función de módulo (no método) — mismo criterio de extracción ya aplicado en todo el BC
    para mantener el CC de `execute()` bajo el umbral de `DesignReviewer`.
    """
    acumulado: dict[UUID, list[int]] = {}
    for respuesta in respuestas:
        if respuesta.pregunta_id not in metadatos:
            continue
        contador = acumulado.setdefault(respuesta.pregunta_id, [0, 0])
        contador[0] += 1
        if not respuesta.es_correcta:
            contador[1] += 1

    filas = [
        RankingPreguntaFallada(
            pregunta_id=pregunta_id,
            enunciado=metadatos[pregunta_id].enunciado,
            unidad_tematica=metadatos[pregunta_id].unidad_tematica,
            tema=metadatos[pregunta_id].tema,
            cantidad_presentaciones=presentaciones,
            cantidad_fallos=fallos,
            tasa_error=fallos / presentaciones,
        )
        for pregunta_id, (presentaciones, fallos) in acumulado.items()
    ]
    return sorted(filas, key=lambda fila: fila.tasa_error, reverse=True)
