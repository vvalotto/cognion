"""Caso de uso: alta de una `ActividadEvaluativaPeriodoAbierto` (US-3.1.2, RF-11)."""

from __future__ import annotations

from datetime import datetime
from uuid import UUID

from src.actividad_evaluativa.entities.actividad_evaluativa_periodo_abierto import (
    ActividadEvaluativaPeriodoAbierto,
)
from src.actividad_evaluativa.entities.errors import MateriaNoExiste, PreguntasInsuficientes
from src.actividad_evaluativa.entities.eventos import ActividadEvaluativaCreada
from src.actividad_evaluativa.entities.ports.event_store_port import (
    EventoParaAlmacenar,
    EventStorePort,
)
from src.actividad_evaluativa.entities.ports.materia_consulta_port import MateriaConsultaPort
from src.actividad_evaluativa.entities.ports.pregunta_consulta_port import PreguntaConsultaPort

AGGREGATE_TYPE = "ActividadEvaluativaPeriodoAbierto"


class CrearActividadPeriodoAbiertoUseCase:
    """Orquesta la creación de la actividad y su persistencia en el event store del BC."""

    def __init__(
        self,
        materia_consulta: MateriaConsultaPort,
        pregunta_consulta: PreguntaConsultaPort,
        event_store: EventStorePort,
    ) -> None:
        """Recibe los puertos de consulta a Banco de Preguntas y el event store del BC."""
        self._materia_consulta = materia_consulta
        self._pregunta_consulta = pregunta_consulta
        self._event_store = event_store

    async def execute(
        self,
        materia_id: UUID,
        fecha_apertura: datetime,
        fecha_cierre: datetime,
        cantidad_preguntas: int,
        cantidad_intentos_permitidos: int,
    ) -> tuple[ActividadEvaluativaPeriodoAbierto, ActividadEvaluativaCreada]:
        """Crea la actividad validando INV-AE-01/02/03 y la persiste como primer evento del stream.

        Levanta `MateriaNoExiste` si `materia_id` no corresponde a ninguna `Materia`,
        `PreguntasInsuficientes` si `cantidad_preguntas` excede las preguntas activas del banco
        de esa materia. `PeriodoInvalido`/`CantidadIntentosInvalida` se validan en el aggregate
        (INV-AE-02/03).
        """
        materia = await self._materia_consulta.obtener(materia_id)
        if materia is None:
            raise MateriaNoExiste(materia_id)

        cantidad_disponible = await self._pregunta_consulta.contar_activas_por_materia(materia_id)
        if cantidad_preguntas > cantidad_disponible:
            raise PreguntasInsuficientes(cantidad_preguntas, cantidad_disponible)

        actividad = ActividadEvaluativaPeriodoAbierto.crear(
            materia_id=materia_id,
            fecha_apertura=fecha_apertura,
            fecha_cierre=fecha_cierre,
            cantidad_preguntas=cantidad_preguntas,
            cantidad_intentos_permitidos=cantidad_intentos_permitidos,
        )

        evento = ActividadEvaluativaCreada(
            actividad_id=actividad.id,
            materia_id=actividad.materia_id,
            fecha_apertura=actividad.fecha_apertura,
            fecha_cierre=actividad.fecha_cierre,
            cantidad_preguntas=actividad.cantidad_preguntas,
            cantidad_intentos_permitidos=actividad.cantidad_intentos_permitidos,
        )

        payload = {
            "actividad_id": str(evento.actividad_id),
            "materia_id": str(evento.materia_id),
            "fecha_apertura": evento.fecha_apertura.isoformat(),
            "fecha_cierre": evento.fecha_cierre.isoformat(),
            "cantidad_preguntas": evento.cantidad_preguntas,
            "cantidad_intentos_permitidos": evento.cantidad_intentos_permitidos,
            "ocurrido_en": evento.ocurrido_en.isoformat(),
        }
        await self._event_store.append(
            AGGREGATE_TYPE,
            actividad.id,
            0,
            [EventoParaAlmacenar(event_type="ActividadEvaluativaCreada", payload=payload)],
        )

        return actividad, evento
