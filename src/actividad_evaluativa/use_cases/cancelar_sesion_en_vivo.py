"""Caso de uso: el Docente cancela una sesión en vivo que nunca inició (US-ADJ-58)."""

from __future__ import annotations

from datetime import UTC, datetime
from uuid import UUID

from src.actividad_evaluativa.entities.actividad_evaluativa_en_vivo import (
    ActividadEvaluativaEnVivo,
)
from src.actividad_evaluativa.entities.errors import (
    ComisionNoAutorizada,
    ConcurrenciaOptimistaError,
    SesionNoExiste,
)
from src.actividad_evaluativa.entities.eventos_en_vivo import SesionEnVivoCancelada
from src.actividad_evaluativa.entities.ports.canal_tiempo_real_port import CanalTiempoRealPort
from src.actividad_evaluativa.entities.ports.comision_consulta_port import ComisionConsultaPort
from src.actividad_evaluativa.entities.ports.event_store_port import (
    EventoParaAlmacenar,
    EventStorePort,
)

AGGREGATE_TYPE_SESION = "ActividadEvaluativaEnVivo"


class CancelarSesionEnVivoUseCase:
    """Orquesta la cancelación: validación (INV-AEV-10), persistencia y aviso por el canal."""

    def __init__(
        self,
        event_store: EventStorePort,
        canal: CanalTiempoRealPort,
        comision_consulta: ComisionConsultaPort,
    ) -> None:
        """Recibe el event store, el canal en vivo y el puerto de Comisión."""
        self._event_store = event_store
        self._canal = canal
        self._comision_consulta = comision_consulta

    async def execute(
        self, sesion_id: UUID, docente_id: UUID | None = None
    ) -> ActividadEvaluativaEnVivo:
        """Cancela la sesión y avisa a los conectados (Estudiantes en la sala de espera).

        Levanta `SesionNoExiste`, `ComisionNoAutorizada` (403) si `docente_id` no está
        asignado a la Comisión de la sesión (`US-ADJ-57`; `None` = Administrador, sin
        chequeo), `SesionYaCancelada` o `SesionYaIniciada`. Si otro comando ganó la carrera de
        escribir en el stream (un inicio o una cancelación simultánea), reintenta una vez sobre
        el stream recargado: la validación devuelve el error del estado real. Publica recién
        después de persistir.
        """
        try:
            sesion = await self._cancelar(sesion_id, docente_id)
        except ConcurrenciaOptimistaError:
            sesion = await self._cancelar(sesion_id, docente_id)

        await self._canal.publicar(sesion_id, {"tipo": "sesion_cancelada"})
        return sesion

    async def _cancelar(
        self, sesion_id: UUID, docente_id: UUID | None
    ) -> ActividadEvaluativaEnVivo:
        """Carga el stream, valida y agrega `SesionEnVivoCancelada`."""
        eventos = await self._event_store.load(AGGREGATE_TYPE_SESION, sesion_id)
        if not eventos:
            raise SesionNoExiste(sesion_id)

        sesion = ActividadEvaluativaEnVivo.reconstruir(eventos)
        if docente_id is not None and not await self._comision_consulta.esta_asignado_a_comision(
            docente_id, sesion.comision_id
        ):
            raise ComisionNoAutorizada(sesion.comision_id)

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
