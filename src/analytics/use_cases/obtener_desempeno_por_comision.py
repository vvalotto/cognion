"""Caso de uso: desempeño de todos los estudiantes de una Comisión (`US-ADJ-44`, RF-20)."""

from __future__ import annotations

from dataclasses import dataclass
from uuid import UUID

from src.analytics.entities.errors import ComisionNoPerteneceAMateria
from src.analytics.entities.ports.comision_consulta_port import (
    ComisionConsultaPort,
    EstudianteResumen,
)
from src.analytics.entities.ports.evaluacion_desempeno_consulta_port import (
    EvaluacionDesempenoConsultaPort,
    EvaluacionDesempenoResumen,
)


@dataclass(frozen=True)
class DesempenoComisionFila:
    """Fila de desempeño de un estudiante del roster de la comisión consultada."""

    estudiante_id: UUID
    nombre: str
    porcentaje_aciertos_acumulado: float | None
    """`None` = "Sin datos" — el estudiante no tiene ninguna `Evaluacion` finalizada en la
    materia. Nunca `0.0`, a diferencia de `ResumenDesempeno.porcentaje_acierto` (`US-4.1.2`),
    que sí devuelve `0` sin datos — acá se distingue explícitamente (`BC-analytics-modelo.md`
    §8.3)."""
    actividades_pendientes: int


class ObtenerDesempenoPorComisionUseCase:
    """Arma una fila por estudiante de la comisión: % acumulado y actividades pendientes.

    Compone `ComisionConsultaPort.listar_estudiantes` (roster) +
    `EvaluacionDesempenoConsultaPort.listar_evaluaciones_finalizadas` (por estudiante) +
    `listar_actividades_abiertas` (una sola vez por comisión) — sin puerto ni evento propio,
    Analytics no tiene aggregate (`BC-analytics-modelo.md` §2).
    """

    def __init__(
        self,
        comision_consulta: ComisionConsultaPort,
        evaluacion_desempeno_consulta: EvaluacionDesempenoConsultaPort,
    ) -> None:
        """Recibe los dos puertos de consulta que compone el agregado."""
        self._comision_consulta = comision_consulta
        self._evaluacion_desempeno_consulta = evaluacion_desempeno_consulta

    async def execute(self, materia_id: UUID, comision_id: UUID) -> list[DesempenoComisionFila]:
        """Devuelve una fila por estudiante del roster de `comision_id`.

        `comision_id` que no pertenece a `materia_id` → `raise ComisionNoPerteneceAMateria`
        (el router lo mapea a 422, mismo criterio que `ObtenerTasaErrorPorTemaUseCase`).
        """
        comisiones = await self._comision_consulta.listar_comisiones_por_materia(materia_id)
        if comision_id not in {comision.id for comision in comisiones}:
            raise ComisionNoPerteneceAMateria(comision_id, materia_id)

        estudiantes = await self._comision_consulta.listar_estudiantes(comision_id)
        actividades_abiertas = (
            await self._evaluacion_desempeno_consulta.listar_actividades_abiertas(
                materia_id, comision_id
            )
        )

        return [
            await self._fila_de(estudiante, materia_id, actividades_abiertas)
            for estudiante in estudiantes
        ]

    async def _fila_de(
        self, estudiante: EstudianteResumen, materia_id: UUID, actividades_abiertas: list[UUID]
    ) -> DesempenoComisionFila:
        """Arma la fila de un estudiante combinando su desempeño y sus pendientes."""
        resumenes = await self._evaluacion_desempeno_consulta.listar_evaluaciones_finalizadas(
            estudiante.id, materia_id
        )
        actividades_finalizadas = {resumen.actividad_id for resumen in resumenes}
        pendientes = sum(
            1
            for actividad_id in actividades_abiertas
            if actividad_id not in actividades_finalizadas
        )

        return DesempenoComisionFila(
            estudiante_id=estudiante.id,
            nombre=estudiante.nombre,
            porcentaje_aciertos_acumulado=_porcentaje_acumulado(resumenes),
            actividades_pendientes=pendientes,
        )


def _porcentaje_acumulado(resumenes: list[EvaluacionDesempenoResumen]) -> float | None:
    """`None` sin ninguna `Evaluacion` finalizada — nunca `0.0` (invariante de esta US)."""
    if not resumenes:
        return None
    total_correctas = sum(resumen.cantidad_correctas for resumen in resumenes)
    total_respuestas = total_correctas + sum(resumen.cantidad_incorrectas for resumen in resumenes)
    if total_respuestas == 0:
        return 0.0
    return round(100 * total_correctas / total_respuestas, 2)
