"""Gateway SQLAlchemy que implementa `SesionesEnVivoQueryPort` (US-6.3.2).

Agrupa los eventos crudos de la tabla `events` en memoria en vez de mantener una proyección
sincronizada aparte — mismo criterio que `SQLAlchemyEvaluacionActivaQueryRepository`
(`US-3.2.4`): a esta escala (una sesión activa por Comisión a la vez) evita una migración
nueva, sin riesgo de que la proyección se desincronice.
"""

from __future__ import annotations

from itertools import groupby
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.actividad_evaluativa.entities.actividad_evaluativa_en_vivo import EstadoSesionEnVivo
from src.actividad_evaluativa.entities.ports.sesiones_en_vivo_query_port import (
    SesionesEnVivoQueryPort,
    SesionEnVivoResumen,
)
from src.actividad_evaluativa.frameworks.db.models import EventoModel

AGGREGATE_TYPE_SESION = "ActividadEvaluativaEnVivo"

_ESTADO_POR_EVENTO = {
    "SesionEnVivoIniciada": EstadoSesionEnVivo.EN_CURSO,
    "SesionEnVivoFinalizada": EstadoSesionEnVivo.FINALIZADA,
}


class SQLAlchemySesionesEnVivoQueryRepository(SesionesEnVivoQueryPort):
    """Deriva el resumen de cada sesión en vivo agrupando `events` en memoria."""

    def __init__(self, session: AsyncSession) -> None:
        """Recibe la sesión async a usar en la consulta."""
        self._session = session

    async def listar(
        self, comision_id: UUID, estados: list[EstadoSesionEnVivo]
    ) -> list[SesionEnVivoResumen]:
        """Agrupa todos los eventos de la sesión por stream, filtra por Comisión y estados."""
        resultado = await self._session.execute(
            select(EventoModel)
            .where(EventoModel.aggregate_type == AGGREGATE_TYPE_SESION)
            .order_by(EventoModel.aggregate_id, EventoModel.sequence_number)
        )
        modelos = resultado.scalars().all()

        resumenes = []
        for _, grupo_iter in groupby(modelos, key=lambda modelo: modelo.aggregate_id):
            resumen = _resumen_de_stream(list(grupo_iter))
            if resumen.comision_id == comision_id and resumen.estado in estados:
                resumenes.append(resumen)
        resumenes.sort(key=lambda resumen: resumen.creada_en, reverse=True)
        return resumenes


def _resumen_de_stream(eventos: list[EventoModel]) -> SesionEnVivoResumen:
    """Deriva un `SesionEnVivoResumen` del stream completo (ya ordenado) de una sesión.

    Extraída a función de módulo, testeable sin sesión de BD (mismo criterio que
    `_resumen_de_stream` en `evaluacion_activa_query_repository.py`).
    """
    primero = eventos[0]
    payload = primero.payload
    estado = EstadoSesionEnVivo.EN_ESPERA
    for evento in eventos:
        estado = _ESTADO_POR_EVENTO.get(evento.event_type, estado)
    return SesionEnVivoResumen(
        id=primero.aggregate_id,
        comision_id=UUID(payload["comision_id"]),
        materia_id=UUID(payload["materia_id"]),
        cantidad_preguntas=len(payload["preguntas"]),
        tiempo_limite_por_pregunta_segundos=payload["tiempo_limite_por_pregunta_segundos"],
        estado=estado,
        creada_en=primero.occurred_at,
        unidad_tematica=payload.get("unidad_tematica"),
        tema=payload.get("tema"),
    )
