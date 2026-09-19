"""Caso de uso: un Estudiante se une a una sesión en vivo (US-6.1.3, RF-08)."""

from __future__ import annotations

from typing import Any
from uuid import UUID

from src.actividad_evaluativa.entities.actividad_evaluativa_en_vivo import (
    ActividadEvaluativaEnVivo,
)
from src.actividad_evaluativa.entities.errors import (
    ConcurrenciaOptimistaError,
    EstudianteNoExiste,
    SesionNoExiste,
)
from src.actividad_evaluativa.entities.eventos_en_vivo import EstudianteUnido
from src.actividad_evaluativa.entities.participacion_en_vivo import ParticipacionEnVivo
from src.actividad_evaluativa.entities.ports.canal_tiempo_real_port import CanalTiempoRealPort
from src.actividad_evaluativa.entities.ports.estudiante_consulta_port import (
    EstudianteConsultaPort,
)
from src.actividad_evaluativa.entities.ports.event_store_port import (
    EventoParaAlmacenar,
    EventStorePort,
)
from src.actividad_evaluativa.entities.ports.participantes_sesion_query_port import (
    ParticipanteResumen,
    ParticipantesSesionQueryPort,
)

AGGREGATE_TYPE_SESION = "ActividadEvaluativaEnVivo"
AGGREGATE_TYPE_PARTICIPACION = "ParticipacionEnVivo"


def _mensaje_participantes(participantes: list[ParticipanteResumen]) -> dict[str, Any]:
    """Arma el mensaje de broadcast con la lista de participantes actualizada (§16)."""
    return {
        "tipo": "participantes_actualizados",
        "cantidad": len(participantes),
        "participantes": [
            {"estudiante_id": str(p.estudiante_id), "unido_en": p.unido_en.isoformat()}
            for p in participantes
        ],
    }


class UnirseASesionEnVivoUseCase:
    """Orquesta la unión (o la reunión idempotente) de un Estudiante a una sesión en vivo."""

    def __init__(
        self,
        estudiante_consulta: EstudianteConsultaPort,
        event_store: EventStorePort,
        participantes_query: ParticipantesSesionQueryPort,
        canal: CanalTiempoRealPort,
    ) -> None:
        """Recibe los puertos de Identidad, el event store, el read model y el canal en vivo."""
        self._estudiante_consulta = estudiante_consulta
        self._event_store = event_store
        self._participantes_query = participantes_query
        self._canal = canal

    async def execute(self, sesion_id: UUID, estudiante_id: UUID) -> ParticipacionEnVivo:
        """Une al Estudiante a la sesión, o devuelve su participación existente (INV-AEV-06).

        Levanta `EstudianteNoExiste` si el actor no es un Estudiante válido, `SesionNoExiste` si
        `sesion_id` no tiene stream y `SesionYaFinalizada` si la sesión ya terminó — una sesión
        `EnEspera` o `EnCurso` admite la unión (unión tardía). Al final publica por el canal en
        vivo la lista de participantes actualizada, también en el caso idempotente; un fallo de
        broadcast no revierte la unión (el canal es best-effort).
        """
        if not await self._estudiante_consulta.existe(estudiante_id):
            raise EstudianteNoExiste(estudiante_id)

        eventos_sesion = await self._event_store.load(AGGREGATE_TYPE_SESION, sesion_id)
        if not eventos_sesion:
            raise SesionNoExiste(sesion_id)
        ActividadEvaluativaEnVivo.reconstruir(eventos_sesion).validar_para_unirse()

        participacion = await self._unir_o_reutilizar(sesion_id, estudiante_id)

        participantes = await self._participantes_query.listar(sesion_id)
        await self._canal.publicar(sesion_id, _mensaje_participantes(participantes))
        return participacion

    async def _unir_o_reutilizar(self, sesion_id: UUID, estudiante_id: UUID) -> ParticipacionEnVivo:
        """Crea la `ParticipacionEnVivo` si no existe; si ya existe, la devuelve sin tocarla."""
        participacion_id = ParticipacionEnVivo.id_para(sesion_id, estudiante_id)
        existentes = await self._event_store.load(AGGREGATE_TYPE_PARTICIPACION, participacion_id)
        if existentes:
            return ParticipacionEnVivo.reconstruir(existentes)

        participacion = ParticipacionEnVivo.unirse(sesion_id, estudiante_id)
        evento = EstudianteUnido.desde_participacion(participacion)
        payload = {
            "sesion_id": str(evento.sesion_id),
            "estudiante_id": str(evento.estudiante_id),
            "unido_en": evento.unido_en.isoformat(),
        }
        try:
            await self._event_store.append(
                AGGREGATE_TYPE_PARTICIPACION,
                participacion.id,
                0,
                [EventoParaAlmacenar(event_type="EstudianteUnido", payload=payload)],
            )
        except ConcurrenciaOptimistaError:
            # Otra unión concurrente (mismo Estudiante, misma sesión) ganó la carrera de insertar
            # el primer evento — releer y devolver esa participación en vez de propagar el error
            # (INV-AEV-06, idempotencia real ante escrituras concurrentes, no solo secuenciales).
            existentes = await self._event_store.load(
                AGGREGATE_TYPE_PARTICIPACION, participacion.id
            )
            return ParticipacionEnVivo.reconstruir(existentes)
        return participacion
