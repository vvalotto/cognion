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
from src.actividad_evaluativa.entities.ports.notificacion_port import NotificacionPort
from src.actividad_evaluativa.entities.ports.pregunta_consulta_port import PreguntaConsultaPort

AGGREGATE_TYPE = "ActividadEvaluativaPeriodoAbierto"


class CrearActividadPeriodoAbiertoUseCase:
    """Orquesta la creación de la actividad y su persistencia en el event store del BC."""

    def __init__(
        self,
        materia_consulta: MateriaConsultaPort,
        pregunta_consulta: PreguntaConsultaPort,
        event_store: EventStorePort,
        notificacion: NotificacionPort,
    ) -> None:
        """Recibe los puertos de consulta a Banco de Preguntas, el event store y Notificaciones."""
        self._materia_consulta = materia_consulta
        self._pregunta_consulta = pregunta_consulta
        self._event_store = event_store
        self._notificacion = notificacion

    async def execute(
        self,
        materia_id: UUID,
        fecha_apertura: datetime,
        fecha_cierre: datetime,
        cantidad_preguntas: int,
        cantidad_intentos_permitidos: int,
        titulo: str = "",
        comisiones_ids: frozenset[UUID] | None = None,
        unidad_tematica: str | None = None,
        tema: str | None = None,
    ) -> tuple[ActividadEvaluativaPeriodoAbierto, object]:
        """Crea la actividad validando INV-AE-01/02/03 y la persiste como primer evento del stream.

        Levanta `MateriaNoExiste` si `materia_id` no corresponde a ninguna `Materia`,
        `PreguntasInsuficientes` si `cantidad_preguntas` excede las preguntas activas del banco
        de esa materia (filtradas por `unidad_tematica`/`tema` si se eligieron, combinados con
        AND). `PeriodoInvalido`/`CantidadIntentosInvalida` se validan en el aggregate
        (INV-AE-02/03). Al final, después de confirmar la persistencia del evento, dispara
        `NotificacionPort.notificar_apertura(...)` (`US-5.1.2`, RF-14) — un fallo de envío no
        revierte ni afecta la respuesta de esta operación.

        El segundo elemento de la tupla se tipa como `object` (no `ActividadEvaluativaCreada`)
        para no acumular CBO en este Use Case — mismo criterio ya aplicado en los controllers
        de `US-2.1.5`/`US-2.1.6`; ningún caller usa su tipo (el router lo descarta).
        """
        materia = await self._materia_consulta.obtener(materia_id)
        if materia is None:
            raise MateriaNoExiste(materia_id)

        cantidad_disponible = await self._pregunta_consulta.contar_activas_por_materia(
            materia_id, unidad_tematica, tema
        )
        if cantidad_preguntas > cantidad_disponible:
            raise PreguntasInsuficientes(cantidad_preguntas, cantidad_disponible)

        actividad = ActividadEvaluativaPeriodoAbierto.crear(
            materia_id=materia_id,
            fecha_apertura=fecha_apertura,
            fecha_cierre=fecha_cierre,
            cantidad_preguntas=cantidad_preguntas,
            cantidad_intentos_permitidos=cantidad_intentos_permitidos,
            titulo=titulo,
            comisiones_ids=comisiones_ids,
            unidad_tematica=unidad_tematica,
            tema=tema,
        )

        evento = ActividadEvaluativaCreada.desde_actividad(actividad)

        payload = {
            "actividad_id": str(evento.actividad_id),
            "materia_id": str(evento.materia_id),
            "fecha_apertura": evento.fecha_apertura.isoformat(),
            "fecha_cierre": evento.fecha_cierre.isoformat(),
            "cantidad_preguntas": evento.cantidad_preguntas,
            "cantidad_intentos_permitidos": evento.cantidad_intentos_permitidos,
            "titulo": evento.titulo,
            "comisiones_ids": [str(c) for c in evento.comisiones_ids],
            "unidad_tematica": evento.unidad_tematica,
            "tema": evento.tema,
            "ocurrido_en": evento.ocurrido_en.isoformat(),
        }
        await self._event_store.append(
            AGGREGATE_TYPE,
            actividad.id,
            0,
            [EventoParaAlmacenar(event_type="ActividadEvaluativaCreada", payload=payload)],
        )

        await self._notificacion.notificar_apertura(
            actividad.id,
            actividad.materia_id,
            materia.nombre,
            actividad.titulo,
            actividad.fecha_apertura,
            actividad.fecha_cierre,
            list(actividad.comisiones_ids),
        )

        return actividad, evento
