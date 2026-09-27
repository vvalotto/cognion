"""Caso de uso: desempeño del Estudiante en una materia, detalle y acumulado (`US-4.1.2`).

`US-ADJ-56` suma las sesiones en vivo `Finalizada` en las que participó, en una sección propia
que no se mezcla con el acumulado de período abierto (`resumen` no cambia).
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from uuid import UUID

from src.analytics.entities.ports.comision_consulta_port import ComisionConsultaPort
from src.analytics.entities.ports.evaluacion_desempeno_consulta_port import (
    EvaluacionDesempenoConsultaPort,
)
from src.analytics.entities.ports.sesion_en_vivo_desempeno_consulta_port import (
    SesionEnVivoDesempenoConsultaPort,
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
class SesionEnVivoDetalle:
    """Fila de detalle de una sesión en vivo `Finalizada` en la que participó el Estudiante."""

    sesion_id: UUID
    comision_horario: str
    finalizada_en: datetime
    cantidad_preguntas: int
    cantidad_correctas: int
    cantidad_incorrectas: int
    puntaje_final: int
    posicion: int
    total_participantes: int


@dataclass(frozen=True)
class DesempenoEstudiante:
    """Respuesta completa que pide RF-15: detalle fila por fila y resumen acumulado.

    `sesiones_en_vivo` (`US-ADJ-56`) no participa de `resumen` — período abierto y modo en vivo
    se muestran separados, decisión de Víctor.
    """

    evaluaciones: list[EvaluacionDetalle]
    resumen: ResumenDesempeno
    sesiones_en_vivo: list[SesionEnVivoDetalle]


class ObtenerDesempenoEstudianteUseCase:
    """Arma el desempeño de un Estudiante en una materia a partir de una única lectura.

    Compone `EvaluacionDesempenoConsultaPort.listar_evaluaciones_finalizadas` (`US-4.1.1`) sin
    una segunda fuente para el acumulado (`BC-analytics-modelo.md` §6, hot spot 3).
    `SesionEnVivoDesempenoConsultaPort` (`US-ADJ-56`) y `ComisionConsultaPort` (para el nombre de
    la comisión, `horario`) alimentan la sección aparte de sesiones en vivo.
    """

    def __init__(
        self,
        evaluacion_desempeno_consulta: EvaluacionDesempenoConsultaPort,
        sesion_en_vivo_desempeno_consulta: SesionEnVivoDesempenoConsultaPort,
        comision_consulta: ComisionConsultaPort,
    ) -> None:
        """Recibe los puertos de consulta de desempeño de período abierto, en vivo y comisión."""
        self._evaluacion_desempeno_consulta = evaluacion_desempeno_consulta
        self._sesion_en_vivo_desempeno_consulta = sesion_en_vivo_desempeno_consulta
        self._comision_consulta = comision_consulta

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
        sesiones_en_vivo = await self._sesiones_en_vivo(estudiante_id, materia_id)
        return DesempenoEstudiante(
            evaluaciones=evaluaciones,
            resumen=_resumen_de(evaluaciones),
            sesiones_en_vivo=sesiones_en_vivo,
        )

    async def _sesiones_en_vivo(
        self, estudiante_id: UUID, materia_id: UUID
    ) -> list[SesionEnVivoDetalle]:
        """Arma el detalle de sesiones en vivo, resolviendo el horario de cada comisión."""
        resumenes = await self._sesion_en_vivo_desempeno_consulta.listar_sesiones_finalizadas(
            estudiante_id, materia_id
        )
        comisiones = await self._comision_consulta.listar_comisiones_por_materia(materia_id)
        horario_por_comision = {comision.id: comision.horario for comision in comisiones}
        ordenados = sorted(resumenes, key=lambda r: r.finalizada_en, reverse=True)
        return [
            SesionEnVivoDetalle(
                sesion_id=r.sesion_id,
                comision_horario=horario_por_comision.get(r.comision_id, ""),
                finalizada_en=r.finalizada_en,
                cantidad_preguntas=r.cantidad_preguntas,
                cantidad_correctas=r.cantidad_correctas,
                cantidad_incorrectas=r.cantidad_incorrectas,
                puntaje_final=r.puntaje_final,
                posicion=r.posicion,
                total_participantes=r.total_participantes,
            )
            for r in ordenados
        ]


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
