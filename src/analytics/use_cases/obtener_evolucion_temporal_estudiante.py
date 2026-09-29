"""Caso de uso: evolución temporal del % de aciertos de un estudiante (`US-ADJ-45`, RF-21)."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from uuid import UUID

from src.analytics.entities.errors import MateriaNoAutorizada
from src.analytics.entities.ports.comision_consulta_port import ComisionConsultaPort
from src.analytics.entities.ports.evaluacion_desempeno_consulta_port import (
    EvaluacionDesempenoConsultaPort,
    EvaluacionDesempenoResumen,
)


@dataclass(frozen=True)
class EvolucionTemporalPunto:
    """Un punto de la serie temporal — una `Evaluacion` finalizada del estudiante."""

    actividad_id: UUID
    titulo_actividad: str
    finalizada_en: datetime
    porcentaje_acierto: int


class ObtenerEvolucionTemporalEstudianteUseCase:
    """Serie temporal individual: una fila por `Evaluacion` finalizada, orden cronológico.

    Reusa `listar_evaluaciones_finalizadas` (`US-4.1.1`) sin fuente adicional — solo reordena
    como serie temporal y resuelve el título de cada actividad
    (`obtener_titulos_actividades`, `US-ADJ-45`).
    """

    def __init__(
        self,
        evaluacion_desempeno_consulta: EvaluacionDesempenoConsultaPort,
        comision_consulta: ComisionConsultaPort,
    ) -> None:
        """Recibe el puerto de consulta de desempeño y el de pertenencia de Comisión."""
        self._evaluacion_desempeno_consulta = evaluacion_desempeno_consulta
        self._comision_consulta = comision_consulta

    async def execute(
        self, estudiante_id: UUID, materia_id: UUID, docente_id: UUID
    ) -> list[EvolucionTemporalPunto]:
        """Devuelve la serie ordenada por `finalizada_en` ascendente.

        Estudiante sin ninguna `Evaluacion` finalizada en la materia → lista vacía.
        `docente_id` sin Comisión asignada en `materia_id` → `raise MateriaNoAutorizada`
        (`US-ADJ-57`).
        """
        if not await self._comision_consulta.esta_asignado_a_materia(docente_id, materia_id):
            raise MateriaNoAutorizada(materia_id)
        resumenes = await self._evaluacion_desempeno_consulta.listar_evaluaciones_finalizadas(
            estudiante_id, materia_id
        )
        if not resumenes:
            return []

        ordenados = sorted(resumenes, key=lambda resumen: resumen.finalizada_en)
        titulos = await self._evaluacion_desempeno_consulta.obtener_titulos_actividades(
            [resumen.actividad_id for resumen in ordenados]
        )
        return [_punto_de(resumen, titulos) for resumen in ordenados]


def _punto_de(
    resumen: EvaluacionDesempenoResumen, titulos: dict[UUID, str]
) -> EvolucionTemporalPunto:
    """Arma un punto de la serie a partir de un resumen ya resuelto."""
    total = resumen.cantidad_correctas + resumen.cantidad_incorrectas
    porcentaje = round(100 * resumen.cantidad_correctas / total) if total > 0 else 0
    return EvolucionTemporalPunto(
        actividad_id=resumen.actividad_id,
        titulo_actividad=titulos.get(resumen.actividad_id, ""),
        finalizada_en=resumen.finalizada_en,
        porcentaje_acierto=porcentaje,
    )
