"""Caso de uso: desempeño del Estudiante en una materia, detalle y acumulado (`US-4.1.2`)."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from uuid import UUID

from src.analytics.entities.ports.evaluacion_desempeno_consulta_port import (
    EvaluacionDesempenoConsultaPort,
)


@dataclass(frozen=True)
class EvaluacionDetalle:
    """Fila de detalle de una `Evaluacion` finalizada, como la expone el puerto de `US-4.1.1`."""

    evaluacion_id: UUID
    actividad_id: UUID
    finalizada_en: datetime
    cantidad_correctas: int
    cantidad_incorrectas: int


@dataclass(frozen=True)
class ResumenDesempeno:
    """Acumulado sobre todas las `Evaluacion` finalizadas devueltas por el detalle."""

    total_correctas: int
    total_incorrectas: int
    porcentaje_acierto: int
    cantidad_evaluaciones: int


@dataclass(frozen=True)
class DesempenoEstudiante:
    """Respuesta completa que pide RF-15: detalle fila por fila y resumen acumulado."""

    evaluaciones: list[EvaluacionDetalle]
    resumen: ResumenDesempeno


class ObtenerDesempenoEstudianteUseCase:
    """Arma el desempeño de un Estudiante en una materia a partir de una única lectura.

    Compone `EvaluacionDesempenoConsultaPort.listar_evaluaciones_finalizadas` (`US-4.1.1`) sin
    una segunda fuente para el acumulado (`BC-analytics-modelo.md` §6, hot spot 3).
    """

    def __init__(self, evaluacion_desempeno_consulta: EvaluacionDesempenoConsultaPort) -> None:
        """Recibe el puerto de consulta de desempeño sobre el event store ajeno."""
        self._evaluacion_desempeno_consulta = evaluacion_desempeno_consulta

    async def execute(self, estudiante_id: UUID, materia_id: UUID) -> DesempenoEstudiante:
        """Devuelve el detalle ordenado por `finalizada_en` descendente y el resumen acumulado."""
        resumenes = await self._evaluacion_desempeno_consulta.listar_evaluaciones_finalizadas(
            estudiante_id, materia_id
        )
        ordenados = sorted(resumenes, key=lambda r: r.finalizada_en, reverse=True)
        evaluaciones = [
            EvaluacionDetalle(
                evaluacion_id=r.evaluacion_id,
                actividad_id=r.actividad_id,
                finalizada_en=r.finalizada_en,
                cantidad_correctas=r.cantidad_correctas,
                cantidad_incorrectas=r.cantidad_incorrectas,
            )
            for r in ordenados
        ]
        return DesempenoEstudiante(evaluaciones=evaluaciones, resumen=_resumen_de(evaluaciones))


def _resumen_de(evaluaciones: list[EvaluacionDetalle]) -> ResumenDesempeno:
    """Suma correctas/incorrectas de las evaluaciones; `porcentaje_acierto` en `0` sin datos."""
    total_correctas = sum(e.cantidad_correctas for e in evaluaciones)
    total_incorrectas = sum(e.cantidad_incorrectas for e in evaluaciones)
    total_respuestas = total_correctas + total_incorrectas
    porcentaje_acierto = (
        round(100 * total_correctas / total_respuestas) if total_respuestas > 0 else 0
    )
    return ResumenDesempeno(
        total_correctas=total_correctas,
        total_incorrectas=total_incorrectas,
        porcentaje_acierto=porcentaje_acierto,
        cantidad_evaluaciones=len(evaluaciones),
    )
