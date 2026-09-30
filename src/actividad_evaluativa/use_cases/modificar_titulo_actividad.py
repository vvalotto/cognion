"""Caso de uso: Docente edita el título de una actividad ya creada (`US-ADJ-10`)."""

from __future__ import annotations

from uuid import UUID

from src.actividad_evaluativa.entities.actividad_evaluativa_periodo_abierto import (
    ActividadEvaluativaPeriodoAbierto,
)
from src.actividad_evaluativa.entities.errors import ActividadNoExiste, MateriaNoAutorizada
from src.actividad_evaluativa.entities.eventos import TituloActividadModificado
from src.actividad_evaluativa.entities.ports.comision_consulta_port import ComisionConsultaPort
from src.actividad_evaluativa.entities.ports.event_store_port import (
    EventoParaAlmacenar,
    EventStorePort,
)

AGGREGATE_TYPE = "ActividadEvaluativaPeriodoAbierto"


class ModificarTituloActividadUseCase:
    """Orquesta la edición de `titulo`.

    Sin invariantes de dominio — a diferencia de `fecha_cierre`.
    """

    def __init__(
        self, event_store: EventStorePort, comision_consulta: ComisionConsultaPort
    ) -> None:
        """Recibe el event store del BC y el puerto de Comisión."""
        self._event_store = event_store
        self._comision_consulta = comision_consulta

    async def execute(
        self, actividad_id: UUID, nuevo_titulo: str, docente_id: UUID | None = None
    ) -> ActividadEvaluativaPeriodoAbierto:
        """Edita `titulo`, sin importar si la actividad está cerrada manualmente.

        Levanta `ActividadNoExiste` si `actividad_id` no tiene stream, `MateriaNoAutorizada`
        (403) si `docente_id` no tiene ninguna Comisión asignada en la materia de la actividad
        (`US-ADJ-57`; `None` = Administrador, sin chequeo).
        """
        eventos = await self._event_store.load(AGGREGATE_TYPE, actividad_id)
        if not eventos:
            raise ActividadNoExiste(actividad_id)

        actividad = ActividadEvaluativaPeriodoAbierto.reconstruir(eventos)

        if docente_id is not None and not await self._comision_consulta.esta_asignado_a_materia(
            docente_id, actividad.materia_id
        ):
            raise MateriaNoAutorizada(actividad.materia_id)

        evento = TituloActividadModificado(actividad_id=actividad_id, nuevo_titulo=nuevo_titulo)
        payload = {
            "actividad_id": str(evento.actividad_id),
            "nuevo_titulo": evento.nuevo_titulo,
            "ocurrido_en": evento.ocurrido_en.isoformat(),
        }
        await self._event_store.append(
            AGGREGATE_TYPE,
            actividad_id,
            len(eventos),
            [EventoParaAlmacenar(event_type="TituloActividadModificado", payload=payload)],
        )

        actividad.titulo = nuevo_titulo
        return actividad
