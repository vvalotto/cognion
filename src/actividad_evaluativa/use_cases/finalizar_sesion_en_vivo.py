"""Caso de uso: el Docente finaliza la sesión en vivo y todos ven el ranking final (US-6.2.7, RF-09)."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any
from uuid import UUID

from src.actividad_evaluativa.entities.actividad_evaluativa_en_vivo import (
    ActividadEvaluativaEnVivo,
)
from src.actividad_evaluativa.entities.errors import (
    ConcurrenciaOptimistaError,
    SesionNoExiste,
    SesionYaFinalizada,
)
from src.actividad_evaluativa.entities.eventos_en_vivo import SesionEnVivoFinalizada
from src.actividad_evaluativa.entities.ports.canal_tiempo_real_port import CanalTiempoRealPort
from src.actividad_evaluativa.entities.ports.event_store_port import (
    EventoParaAlmacenar,
    EventStorePort,
)
from src.actividad_evaluativa.entities.ports.proyecciones_en_vivo_port import (
    ParticipanteEnRanking,
    ProyeccionesEnVivoQueryPort,
)

AGGREGATE_TYPE_SESION = "ActividadEvaluativaEnVivo"


def _payload(evento: SesionEnVivoFinalizada) -> dict[str, Any]:
    """Arma el payload persistido de `SesionEnVivoFinalizada` (sin ranking)."""
    return {
        "sesion_id": str(evento.sesion_id),
        "ocurrido_en": evento.ocurrido_en.isoformat(),
    }


def _mensaje_final(ranking: list[ParticipanteEnRanking]) -> dict[str, Any]:
    """Arma el broadcast de cierre de la sesión con el ranking final (§16)."""
    return {
        "tipo": "sesion_finalizada",
        "ranking": [
            {
                "posicion": r.posicion,
                "estudiante_id": str(r.estudiante_id),
                "puntaje_acumulado": r.puntaje_acumulado,
            }
            for r in ranking
        ],
    }


class FinalizarSesionEnVivoUseCase:
    """Orquesta la finalización: validación, persistencia y broadcast del ranking final."""

    def __init__(
        self,
        event_store: EventStorePort,
        proyecciones: ProyeccionesEnVivoQueryPort,
        canal: CanalTiempoRealPort,
    ) -> None:
        """Recibe el event store, la lectura de proyecciones y el canal de tiempo real."""
        self._event_store = event_store
        self._proyecciones = proyecciones
        self._canal = canal

    async def execute(self, sesion_id: UUID) -> ActividadEvaluativaEnVivo:
        """Finaliza la sesión y transmite el ranking final a todos los conectados.

        Levanta `SesionNoExiste`, `SesionYaFinalizada` (incluida la carrera de dos
        finalizaciones simultáneas, que el chequeo optimista resuelve dejando ganar a una),
        `SesionNoEnCurso` o `PreguntaActualNoCerrada`. Publica recién después de persistir.
        """
        eventos = await self._event_store.load(AGGREGATE_TYPE_SESION, sesion_id)
        if not eventos:
            raise SesionNoExiste(sesion_id)

        sesion = ActividadEvaluativaEnVivo.reconstruir(eventos)
        sesion.finalizar()
        evento = SesionEnVivoFinalizada.desde_sesion(sesion, datetime.now(UTC))

        try:
            await self._event_store.append(
                AGGREGATE_TYPE_SESION,
                sesion_id,
                len(eventos),
                [
                    EventoParaAlmacenar(
                        event_type="SesionEnVivoFinalizada", payload=_payload(evento)
                    )
                ],
            )
        except ConcurrenciaOptimistaError as exc:
            raise SesionYaFinalizada(sesion_id) from exc

        ranking = await self._proyecciones.ranking(sesion_id)
        await self._canal.publicar(sesion_id, _mensaje_final(ranking))
        return sesion
