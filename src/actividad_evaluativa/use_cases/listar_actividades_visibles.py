"""Caso de uso: actividades visibles para el Estudiante, con estado por-estudiante (`US-3.4.5`)."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from uuid import UUID

from src.actividad_evaluativa.entities.evaluacion import Evaluacion
from src.actividad_evaluativa.entities.ports.actividad_query_port import (
    ActividadQueryPort,
    ActividadResumen,
)
from src.actividad_evaluativa.entities.ports.evaluacion_estudiante_query_port import (
    EvaluacionEstudianteQueryPort,
)

EstadoVisible = str
"""`"pendiente" | "todavia_no_abrio" | "finalizada"` (ver `_estado_para`)."""


@dataclass(frozen=True)
class ActividadVisible:
    """Resumen de una actividad más el estado desde la perspectiva del Estudiante autenticado."""

    id: UUID
    materia_id: UUID
    titulo: str
    fecha_apertura: datetime
    fecha_cierre: datetime
    estado: EstadoVisible
    evaluacion_id: UUID | None
    """El id de la `Evaluacion` Finalizada del Estudiante, para navegar a su revisión; `None`
    en cualquier otro estado."""


class ListarActividadesVisiblesUseCase:
    """Extiende `ListarActividadesUseCase` (`US-3.4.2`) con el estado por-estudiante."""

    def __init__(
        self,
        actividad_query: ActividadQueryPort,
        evaluacion_query: EvaluacionEstudianteQueryPort,
    ) -> None:
        """Recibe el puerto de consulta de actividades y el de evaluaciones finalizadas."""
        self._actividad_query = actividad_query
        self._evaluacion_query = evaluacion_query

    async def execute(self, materia_id: UUID, estudiante_id: UUID) -> list[ActividadVisible]:
        """Devuelve cada actividad de `materia_id` con el `Badge` del Estudiante `estudiante_id`."""
        resumenes = await self._actividad_query.listar_por_materia(materia_id)
        evaluacion_id_por_actividad = {
            resumen.id: Evaluacion.id_para(resumen.id, estudiante_id) for resumen in resumenes
        }
        finalizadas = await self._evaluacion_query.existentes_finalizadas(
            list(evaluacion_id_por_actividad.values())
        )

        ahora = datetime.now(UTC)
        return [
            _a_visible(resumen, evaluacion_id_por_actividad[resumen.id], finalizadas, ahora)
            for resumen in resumenes
        ]


def _a_visible(
    resumen: ActividadResumen, evaluacion_id: UUID, finalizadas: set[UUID], ahora: datetime
) -> ActividadVisible:
    """Arma un `ActividadVisible`, extraída para mantener `execute` legible sin sesión de BD."""
    finalizada = evaluacion_id in finalizadas
    return ActividadVisible(
        id=resumen.id,
        materia_id=resumen.materia_id,
        titulo=resumen.titulo,
        fecha_apertura=resumen.fecha_apertura,
        fecha_cierre=resumen.fecha_cierre,
        estado=_estado_para(resumen, finalizada, ahora),
        evaluacion_id=evaluacion_id if finalizada else None,
    )


def _estado_para(resumen: ActividadResumen, finalizada: bool, ahora: datetime) -> EstadoVisible:
    """Deriva el `Badge` del Estudiante — solo 3 estados, fieles al prototipo aprobado.

    Ver `docs/design/ux/prototipos/actividad-evaluativa-periodo-abierto.html` `#est-actividades`.
    `"finalizada"` si ya tiene una `Evaluacion` `Finalizada`; `"todavia_no_abrio"` con
    `fecha_apertura` futura; `"pendiente"` en cualquier otro caso — incluye tanto el período
    vigente como una actividad ya cerrada sin que el Estudiante haya rendido (ese caso se
    resuelve recién al intentar iniciar, `US-3.4.6`, con el 422 de `FueraDePeriodo` — no hay un
    badge propio para "cerrada sin rendir" en la grilla, mismo criterio que
    `EnCurso`/`Suspendida` no distinguidas).
    """
    if finalizada:
        return "finalizada"
    if resumen.fecha_apertura > ahora:
        return "todavia_no_abrio"
    return "pendiente"
