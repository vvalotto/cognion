"""Caso de uso: evolución temporal del % de aciertos promedio de una Comisión.

US-ADJ-45, RF-21.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from uuid import UUID

from src.analytics.entities.errors import ComisionNoPerteneceAMateria
from src.analytics.entities.ports.comision_consulta_port import ComisionConsultaPort
from src.analytics.entities.ports.evaluacion_desempeno_consulta_port import (
    EvaluacionDesempenoConsultaPort,
    EvaluacionDesempenoResumen,
)


@dataclass(frozen=True)
class EvolucionTemporalComisionPunto:
    """Un punto de la serie temporal de la comisión — una actividad con al menos 1 finalizada."""

    actividad_id: UUID
    titulo_actividad: str
    porcentaje_aciertos_promedio: float


class ObtenerEvolucionTemporalComisionUseCase:
    """Serie temporal de comisión: promedio simple por actividad entre quienes la finalizaron.

    Quien no rindió una actividad no entra a su promedio — no cuenta como 0%. Ordena por
    `min(finalizada_en)` del grupo, proxy de orden cronológico (`BC-analytics-modelo.md` §8.4,
    hot spot 2).
    """

    def __init__(
        self,
        comision_consulta: ComisionConsultaPort,
        evaluacion_desempeno_consulta: EvaluacionDesempenoConsultaPort,
    ) -> None:
        """Recibe los dos puertos de consulta que compone el agregado."""
        self._comision_consulta = comision_consulta
        self._evaluacion_desempeno_consulta = evaluacion_desempeno_consulta

    async def execute(
        self, materia_id: UUID, comision_id: UUID
    ) -> list[EvolucionTemporalComisionPunto]:
        """Devuelve la serie ordenada cronológicamente por actividad.

        `comision_id` que no pertenece a `materia_id` → `raise ComisionNoPerteneceAMateria`.
        """
        comisiones = await self._comision_consulta.listar_comisiones_por_materia(materia_id)
        if comision_id not in {comision.id for comision in comisiones}:
            raise ComisionNoPerteneceAMateria(comision_id, materia_id)

        estudiantes = await self._comision_consulta.listar_estudiantes(comision_id)
        por_actividad: dict[UUID, list[tuple[int, datetime]]] = {}
        for estudiante in estudiantes:
            resumenes = await self._evaluacion_desempeno_consulta.listar_evaluaciones_finalizadas(
                estudiante.id, materia_id
            )
            _acumular_por_actividad(por_actividad, resumenes)

        if not por_actividad:
            return []

        titulos = await self._evaluacion_desempeno_consulta.obtener_titulos_actividades(
            list(por_actividad.keys())
        )
        return _puntos_ordenados(por_actividad, titulos)


def _acumular_por_actividad(
    por_actividad: dict[UUID, list[tuple[int, datetime]]],
    resumenes: list[EvaluacionDesempenoResumen],
) -> None:
    """Agrega, por `actividad_id`, el % de acierto y `finalizada_en` de cada resumen.

    Función de módulo (no método) — mantiene el CC de `execute` bajo el umbral de
    `DesignReviewer`, mismo criterio ya aplicado en el resto del BC.
    """
    for resumen in resumenes:
        total = resumen.cantidad_correctas + resumen.cantidad_incorrectas
        porcentaje = round(100 * resumen.cantidad_correctas / total) if total > 0 else 0
        por_actividad.setdefault(resumen.actividad_id, []).append(
            (porcentaje, resumen.finalizada_en)
        )


def _puntos_ordenados(
    por_actividad: dict[UUID, list[tuple[int, datetime]]], titulos: dict[UUID, str]
) -> list[EvolucionTemporalComisionPunto]:
    """Arma un punto por actividad y ordena por `min(finalizada_en)` del grupo, ascendente."""
    con_orden = [
        (
            min(finalizada_en for _, finalizada_en in valores),
            EvolucionTemporalComisionPunto(
                actividad_id=actividad_id,
                titulo_actividad=titulos.get(actividad_id, ""),
                porcentaje_aciertos_promedio=sum(p for p, _ in valores) / len(valores),
            ),
        )
        for actividad_id, valores in por_actividad.items()
    ]
    con_orden.sort(key=lambda item: item[0])
    return [punto for _, punto in con_orden]
