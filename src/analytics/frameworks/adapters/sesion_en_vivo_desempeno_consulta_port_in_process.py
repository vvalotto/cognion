"""Adapter que implementa `SesionEnVivoDesempenoConsultaPort` leyendo el event store ajeno.

Segundo adapter de Analytics que importa código de Actividad Evaluativa (junto a
`EvaluacionDesempenoConsultaPortInProcess`, `US-4.1.1`) — mismo criterio: sin invocar ningún
Use Case de esa BC, agrupando `EventoModel` en memoria. Además lee `RankingPorSesionModel`
(read model `ranking_por_sesion`, `US-6.2.3`) para `posicion`/`total_participantes`, en vez de
reimplementar el desempate ya resuelto por `SQLAlchemyProyeccionesEnVivoRepository.ranking()`
(`docs/specs/ajustes/US-ADJ-56.md`).
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from itertools import groupby
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.actividad_evaluativa.entities.actividad_evaluativa_en_vivo import (
    ActividadEvaluativaEnVivo,
    EstadoSesionEnVivo,
)
from src.actividad_evaluativa.entities.participacion_en_vivo import ParticipacionEnVivo
from src.actividad_evaluativa.entities.ports.event_store_port import EventoAlmacenado
from src.actividad_evaluativa.frameworks.db.models import EventoModel, RankingPorSesionModel
from src.analytics.entities.ports.sesion_en_vivo_desempeno_consulta_port import (
    SesionEnVivoDesempenoConsultaPort,
    SesionEnVivoDesempenoResumen,
)

AGGREGATE_TYPE_SESION = "ActividadEvaluativaEnVivo"
AGGREGATE_TYPE_PARTICIPACION = "ParticipacionEnVivo"
EVENT_TYPE_ESTUDIANTE_UNIDO = "EstudianteUnido"
EVENT_TYPE_SESION_FINALIZADA = "SesionEnVivoFinalizada"


@dataclass(frozen=True)
class _SesionFinalizada:
    """Par (sesión reconstruida, fecha de finalización) — evita recalcular `finalizada_en`."""

    sesion: ActividadEvaluativaEnVivo
    finalizada_en: datetime


class SesionEnVivoDesempenoConsultaPortInProcess(SesionEnVivoDesempenoConsultaPort):
    """Deriva el desempeño en vivo agrupando `events` y `ranking_por_sesion` en memoria."""

    def __init__(self, session: AsyncSession) -> None:
        """Recibe la sesión async compartida con el event store de Actividad Evaluativa."""
        self._session = session

    async def listar_sesiones_finalizadas(
        self, estudiante_id: UUID, materia_id: UUID | None
    ) -> list[SesionEnVivoDesempenoResumen]:
        """Ver `SesionEnVivoDesempenoConsultaPort.listar_sesiones_finalizadas`."""
        participaciones = _streams_de_estudiante(
            await _todos_los_streams_participacion(self._session), estudiante_id
        )
        if not participaciones:
            return []

        sesion_ids = {UUID(eventos[0].payload["sesion_id"]) for eventos in participaciones}
        sesiones_finalizadas = await _sesiones_finalizadas(self._session, sesion_ids, materia_id)
        if not sesiones_finalizadas:
            return []

        ranking_por_sesion = await _ranking_por_sesion(self._session, set(sesiones_finalizadas))
        return _resumenes(participaciones, sesiones_finalizadas, ranking_por_sesion)


async def _todos_los_streams_participacion(session: AsyncSession) -> list[list[EventoModel]]:
    """Agrupa todos los eventos de `ParticipacionEnVivo` por stream, ordenados dentro de cada uno.

    Función de módulo (no método) — mismo criterio de WMC que
    `EvaluacionDesempenoConsultaPortInProcess`.
    """
    resultado = await session.execute(
        select(EventoModel)
        .where(EventoModel.aggregate_type == AGGREGATE_TYPE_PARTICIPACION)
        .order_by(EventoModel.aggregate_id, EventoModel.sequence_number)
    )
    modelos = resultado.scalars().all()

    streams = []
    for _, grupo_iter in groupby(modelos, key=lambda modelo: modelo.aggregate_id):
        eventos = list(grupo_iter)
        if eventos[0].event_type != EVENT_TYPE_ESTUDIANTE_UNIDO:
            continue
        streams.append(eventos)
    return streams


def _streams_de_estudiante(
    streams: list[list[EventoModel]], estudiante_id: UUID
) -> list[list[EventoModel]]:
    """Filtra los streams de `ParticipacionEnVivo` que pertenecen al estudiante indicado."""
    return [
        eventos for eventos in streams if eventos[0].payload["estudiante_id"] == str(estudiante_id)
    ]


async def _sesiones_finalizadas(
    session: AsyncSession, sesion_ids: set[UUID], materia_id: UUID | None
) -> dict[UUID, _SesionFinalizada]:
    """Reconstruye las sesiones de `sesion_ids` que están `Finalizada`, filtradas por materia.

    Función de módulo (no método) — mismo criterio de WMC que el resto de este archivo.
    """
    resultado = await session.execute(
        select(EventoModel)
        .where(
            EventoModel.aggregate_type == AGGREGATE_TYPE_SESION,
            EventoModel.aggregate_id.in_(sesion_ids),
        )
        .order_by(EventoModel.aggregate_id, EventoModel.sequence_number)
    )
    modelos = resultado.scalars().all()

    sesiones: dict[UUID, _SesionFinalizada] = {}
    for aggregate_id, grupo_iter in groupby(modelos, key=lambda modelo: modelo.aggregate_id):
        modelos_stream = list(grupo_iter)
        sesion = ActividadEvaluativaEnVivo.reconstruir(
            [_a_evento_almacenado(modelo) for modelo in modelos_stream]
        )
        if sesion.estado != EstadoSesionEnVivo.FINALIZADA:
            continue
        if materia_id is not None and sesion.materia_id != materia_id:
            continue
        evento_finalizada = next(
            modelo for modelo in modelos_stream if modelo.event_type == EVENT_TYPE_SESION_FINALIZADA
        )
        sesiones[aggregate_id] = _SesionFinalizada(
            sesion=sesion, finalizada_en=evento_finalizada.occurred_at
        )
    return sesiones


async def _ranking_por_sesion(
    session: AsyncSession, sesion_ids: set[UUID]
) -> dict[UUID, list[RankingPorSesionModel]]:
    """Lee `ranking_por_sesion` de las sesiones dadas, ya ordenado por sesión.

    Mismo criterio de desempate que `SQLAlchemyProyeccionesEnVivoRepository.ranking()`:
    puntaje descendente, última actualización ascendente, estudiante ascendente. Función de
    módulo (no método) — mismo criterio de WMC que el resto de este archivo.
    """
    resultado = await session.execute(
        select(RankingPorSesionModel)
        .where(RankingPorSesionModel.sesion_id.in_(sesion_ids))
        .order_by(
            RankingPorSesionModel.sesion_id,
            RankingPorSesionModel.puntaje_acumulado.desc(),
            RankingPorSesionModel.ultima_actualizacion.asc(),
            RankingPorSesionModel.estudiante_id.asc(),
        )
    )
    agrupado: dict[UUID, list[RankingPorSesionModel]] = {}
    for modelo in resultado.scalars().all():
        agrupado.setdefault(modelo.sesion_id, []).append(modelo)
    return agrupado


def _resumenes(
    participaciones: list[list[EventoModel]],
    sesiones_finalizadas: dict[UUID, _SesionFinalizada],
    ranking_por_sesion: dict[UUID, list[RankingPorSesionModel]],
) -> list[SesionEnVivoDesempenoResumen]:
    """Arma un resumen por cada participación cuya sesión está `Finalizada`.

    Función de módulo (no método) — mismo criterio de WMC que el resto de este archivo.
    """
    resumenes = []
    for eventos in participaciones:
        sesion_id = UUID(eventos[0].payload["sesion_id"])
        sesion_finalizada = sesiones_finalizadas.get(sesion_id)
        if sesion_finalizada is None:
            continue
        resumen = _resumen_de_participacion(
            eventos, sesion_finalizada, ranking_por_sesion.get(sesion_id, [])
        )
        if resumen is not None:
            resumenes.append(resumen)
    return resumenes


def _resumen_de_participacion(
    eventos: list[EventoModel],
    sesion_finalizada: _SesionFinalizada,
    ranking: list[RankingPorSesionModel],
) -> SesionEnVivoDesempenoResumen | None:
    """Deriva el resumen de una participación ya emparejada con su sesión `Finalizada`.

    Función de módulo (no método) — mismo criterio de WMC que el resto de este archivo.
    `None` si el estudiante no tiene fila en `ranking_por_sesion` (no debería ocurrir:
    `UnirseASesionEnVivoUseCase` la inicializa al unirse, `US-6.2.3`).
    """
    participacion = ParticipacionEnVivo.reconstruir(
        [_a_evento_almacenado(modelo) for modelo in eventos]
    )
    posicion = next(
        (
            i
            for i, fila in enumerate(ranking, start=1)
            if fila.estudiante_id == participacion.estudiante_id
        ),
        None,
    )
    if posicion is None:
        return None

    correctas = sum(1 for respuesta in participacion.respuestas if respuesta.es_correcta)
    incorrectas = len(participacion.respuestas) - correctas
    sesion = sesion_finalizada.sesion

    return SesionEnVivoDesempenoResumen(
        sesion_id=sesion.id,
        comision_id=sesion.comision_id,
        materia_id=sesion.materia_id,
        finalizada_en=sesion_finalizada.finalizada_en,
        cantidad_preguntas=len(sesion.preguntas),
        cantidad_correctas=correctas,
        cantidad_incorrectas=incorrectas,
        puntaje_final=participacion.puntaje_acumulado,
        posicion=posicion,
        total_participantes=len(ranking),
    )


def _a_evento_almacenado(evento: EventoModel) -> EventoAlmacenado:
    """Adapta una fila `EventoModel` (ORM) al DTO puro que espera `.reconstruir()`."""
    return EventoAlmacenado(
        sequence_number=evento.sequence_number,
        event_type=evento.event_type,
        payload=evento.payload,
        occurred_at=evento.occurred_at,
    )
