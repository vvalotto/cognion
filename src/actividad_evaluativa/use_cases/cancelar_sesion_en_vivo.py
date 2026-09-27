"""Caso de uso: el Docente cancela una sesión en vivo que nunca inició (US-ADJ-58)."""

from __future__ import annotations

from datetime import UTC, datetime
from uuid import UUID

from src.actividad_evaluativa.entities.actividad_evaluativa_en_vivo import (
    ActividadEvaluativaEnVivo,
)
from src.actividad_evaluativa.entities.errors import ConcurrenciaOptimistaError, SesionNoExiste
from src.actividad_evaluativa.entities.eventos_en_vivo import SesionEnVivoCancelada
from src.actividad_evaluativa.entities.ports.canal_tiempo_real_port import CanalTiempoRealPort
from src.actividad_evaluativa.entities.ports.event_store_port import (
    EventoParaAlmacenar,
    EventStorePort,
)

AGGREGATE_TYPE_SESION = "ActividadEvaluativaEnVivo"


class CancelarSesionEnVivoUseCase:
    """Orquesta la cancelación: validación (INV-AEV-10), persistencia y aviso por el canal."""

    def __init__(self, event_store: EventStorePort, canal: CanalTiempoRealPort) -> None:
        """Recibe el event store y el canal en vivo."""
        self._event_store = event_store
        self._canal = canal

    async def execute(self, sesion_id: UUID) -> ActividadEvaluativaEnVivo:
        """Cancela la sesión y avisa a los conectados (Estudiantes en la sala de espera).

        Levanta `SesionNoExiste`, `SesionYaCancelada` o `SesionYaIniciada`. Si otro comando ganó
        la carrera de escribir en el stream (un inicio o una cancelación simultánea), reintenta
        una vez sobre el stream recargado: la validación devuelve el error del estado real.
        Publica recién después de persistir.
        """
        try:
            sesion = await self._cancelar(sesion_id)
        except ConcurrenciaOptimistaError:
            sesion = await self._cancelar(sesion_id)

        await self._canal.publicar(sesion_id, {"tipo": "sesion_cancelada"})
        return sesion

    async def _cancelar(self, sesion_id: UUID) -> ActividadEvaluativaEnVivo:
        """Carga el stream, valida y agrega `SesionEnVivoCancelada`."""
        eventos = await self._event_store.load(AGGREGATE_TYPE_SESION, sesion_id)
        if not eventos:
            raise SesionNoExiste(sesion_id)

        sesion = ActividadEvaluativaEnVivo.reconstruir(eventos)
        sesion.cancelar()
        evento = SesionEnVivoCancelada.desde_sesion(sesion, datetime.now(UTC))
        await self._event_store.append(
            AGGREGATE_TYPE_SESION,
            sesion_id,
            len(eventos),
            [
                EventoParaAlmacenar(
                    event_type="SesionEnVivoCancelada",
                    payload={
                        "sesion_id": str(evento.sesion_id),
                        "ocurrido_en": evento.ocurrido_en.isoformat(),
                    },
                )
            ],
        )
        return sesion
