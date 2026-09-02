"""Caso de uso: Docente modifica el período de disponibilidad de una actividad (RF-11b)."""

from __future__ import annotations

from datetime import datetime
from uuid import UUID

from src.actividad_evaluativa.entities.actividad_evaluativa_periodo_abierto import (
    ActividadEvaluativaPeriodoAbierto,
)
from src.actividad_evaluativa.entities.errors import ActividadNoExiste
from src.actividad_evaluativa.entities.eventos import PeriodoDisponibilidadModificado
from src.actividad_evaluativa.entities.ports.evaluacion_activa_query_port import (
    EvaluacionActivaQueryPort,
)
from src.actividad_evaluativa.entities.ports.event_store_port import (
    EventoParaAlmacenar,
    EventStorePort,
)

AGGREGATE_TYPE = "ActividadEvaluativaPeriodoAbierto"


class ModificarPeriodoDisponibilidadUseCase:
    """Orquesta la extensión/acortamiento de `fecha_cierre` (INV-AE-02/04/04b)."""

    def __init__(
        self,
        event_store: EventStorePort,
        evaluacion_activa_query: EvaluacionActivaQueryPort,
    ) -> None:
        """Recibe el event store del BC y el read model de evaluaciones activas (`US-3.2.4`)."""
        self._event_store = event_store
        self._evaluacion_activa_query = evaluacion_activa_query

    async def execute(
        self, actividad_id: UUID, nueva_fecha_cierre: datetime
    ) -> ActividadEvaluativaPeriodoAbierto:
        """Modifica `fecha_cierre`, o levanta el error de dominio correspondiente.

        Levanta `ActividadNoExiste` si `actividad_id` no tiene stream. Delega en
        `ActividadEvaluativaPeriodoAbierto.validar_para_modificar_periodo` la validación de
        `PeriodoInvalido` (INV-AE-02), `NoSePuedeAcortarConEvaluacionesActivas` (INV-AE-04) y
        `ActividadYaCerrada` (INV-AE-04b).
        """
        eventos = await self._event_store.load(AGGREGATE_TYPE, actividad_id)
        if not eventos:
            raise ActividadNoExiste(actividad_id)

        actividad = ActividadEvaluativaPeriodoAbierto.reconstruir(eventos)

        resumen = await self._evaluacion_activa_query.listar_no_finalizadas()
        hay_evaluaciones_activas = any(item.actividad_id == actividad_id for item in resumen)

        actividad.validar_para_modificar_periodo(nueva_fecha_cierre, hay_evaluaciones_activas)

        evento = PeriodoDisponibilidadModificado(
            actividad_id=actividad_id, nueva_fecha_cierre=nueva_fecha_cierre
        )
        payload = {
            "actividad_id": str(evento.actividad_id),
            "nueva_fecha_cierre": evento.nueva_fecha_cierre.isoformat(),
            "ocurrido_en": evento.ocurrido_en.isoformat(),
        }
        await self._event_store.append(
            AGGREGATE_TYPE,
            actividad_id,
            len(eventos),
            [EventoParaAlmacenar(event_type="PeriodoDisponibilidadModificado", payload=payload)],
        )

        actividad.fecha_cierre = nueva_fecha_cierre
        return actividad
