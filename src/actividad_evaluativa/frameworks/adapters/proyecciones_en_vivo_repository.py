"""Gateway SQLAlchemy que implementa los puertos de proyecciones de la sesión en vivo (US-6.2.3).

Dos adapters (command/query, mismo criterio que `EvaluacionActivaQueryPort` de `US-3.2.4`) sobre
los dos read models: `SQLAlchemyProyeccionesEnVivo` escribe y `SQLAlchemyProyeccionesEnVivoQuery`
lee. Las escrituras son upserts
atómicos en la base (`ON CONFLICT`), nunca leer-modificar-escribir en Python, y no hacen
`commit`: quedan pendientes en la sesión hasta que `EventStorePort.append` confirma el evento.
"""

from __future__ import annotations

from datetime import UTC, datetime
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession

from src.actividad_evaluativa.entities.ports.proyecciones_en_vivo_port import (
    OpcionDistribuida,
    ParticipanteEnRanking,
    ProyeccionesEnVivoPort,
    ProyeccionesEnVivoQueryPort,
)
from src.actividad_evaluativa.frameworks.db.models import (
    DistribucionPorPreguntaModel,
    RankingPorSesionModel,
)


class SQLAlchemyProyeccionesEnVivo(ProyeccionesEnVivoPort):
    """Escribe `ranking_por_sesion` y `distribucion_por_pregunta` (sin `commit`)."""

    def __init__(self, session: AsyncSession) -> None:
        """Recibe la sesión async compartida con el event store (misma unidad de trabajo)."""
        self._session = session

    async def inicializar_participante(self, sesion_id: UUID, estudiante_id: UUID) -> None:
        """Inserta la fila del ranking con 0 puntos; `DO NOTHING` si ya existe."""
        await self._session.execute(
            insert(RankingPorSesionModel)
            .values(
                sesion_id=sesion_id,
                estudiante_id=estudiante_id,
                puntaje_acumulado=0,
                ultima_actualizacion=datetime.now(UTC),
            )
            .on_conflict_do_nothing(index_elements=["sesion_id", "estudiante_id"])
        )

    async def registrar_respuesta(
        self,
        sesion_id: UUID,
        estudiante_id: UUID,
        pregunta_id: UUID,
        opcion: str,
        puntaje: int,
    ) -> None:
        """Suma `puntaje` al ranking y 1 a la opción elegida, ambos como upserts atómicos."""
        ahora = datetime.now(UTC)
        ranking = insert(RankingPorSesionModel).values(
            sesion_id=sesion_id,
            estudiante_id=estudiante_id,
            puntaje_acumulado=puntaje,
            ultima_actualizacion=ahora,
        )
        await self._session.execute(
            ranking.on_conflict_do_update(
                index_elements=["sesion_id", "estudiante_id"],
                set_={
                    "puntaje_acumulado": RankingPorSesionModel.puntaje_acumulado
                    + ranking.excluded.puntaje_acumulado,
                    "ultima_actualizacion": ahora,
                },
            )
        )
        distribucion = insert(DistribucionPorPreguntaModel).values(
            sesion_id=sesion_id, pregunta_id=pregunta_id, opcion=opcion, cantidad=1
        )
        await self._session.execute(
            distribucion.on_conflict_do_update(
                index_elements=["sesion_id", "pregunta_id", "opcion"],
                set_={"cantidad": DistribucionPorPreguntaModel.cantidad + 1},
            )
        )

    async def descartar_pendientes(self) -> None:
        """Hace rollback de la sesión: descarta la proyección todavía no confirmada."""
        await self._session.rollback()


class SQLAlchemyProyeccionesEnVivoQuery(ProyeccionesEnVivoQueryPort):
    """Consulta de solo lectura de `ranking_por_sesion` y `distribucion_por_pregunta`."""

    def __init__(self, session: AsyncSession) -> None:
        """Recibe la sesión async a usar en las consultas."""
        self._session = session

    async def ranking(self, sesion_id: UUID) -> list[ParticipanteEnRanking]:
        """Devuelve el ranking ordenado, con la posición calculada al leer."""
        resultado = await self._session.execute(
            select(RankingPorSesionModel)
            .where(RankingPorSesionModel.sesion_id == sesion_id)
            .order_by(
                RankingPorSesionModel.puntaje_acumulado.desc(),
                RankingPorSesionModel.ultima_actualizacion.asc(),
                RankingPorSesionModel.estudiante_id.asc(),
            )
        )
        return [
            ParticipanteEnRanking(
                posicion=posicion,
                estudiante_id=modelo.estudiante_id,
                puntaje_acumulado=modelo.puntaje_acumulado,
            )
            for posicion, modelo in enumerate(resultado.scalars().all(), start=1)
        ]

    async def distribucion(self, sesion_id: UUID, pregunta_id: UUID) -> list[OpcionDistribuida]:
        """Devuelve la cantidad de respuestas por opción, ordenada por opción."""
        resultado = await self._session.execute(
            select(DistribucionPorPreguntaModel)
            .where(
                DistribucionPorPreguntaModel.sesion_id == sesion_id,
                DistribucionPorPreguntaModel.pregunta_id == pregunta_id,
            )
            .order_by(DistribucionPorPreguntaModel.opcion)
        )
        return [
            OpcionDistribuida(opcion=modelo.opcion, cantidad=modelo.cantidad)
            for modelo in resultado.scalars().all()
        ]

    async def cantidad_respuestas(self, sesion_id: UUID, pregunta_id: UUID) -> int:
        """Devuelve el total de respuestas de la pregunta."""
        total = await self._session.scalar(
            select(func.coalesce(func.sum(DistribucionPorPreguntaModel.cantidad), 0)).where(
                DistribucionPorPreguntaModel.sesion_id == sesion_id,
                DistribucionPorPreguntaModel.pregunta_id == pregunta_id,
            )
        )
        return int(total or 0)
