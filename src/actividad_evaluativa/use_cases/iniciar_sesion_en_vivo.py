"""Caso de uso: el Docente inicia una sesión en vivo (US-6.1.4, RF-08)."""

from __future__ import annotations

from typing import Any
from uuid import UUID

from src.actividad_evaluativa.entities.actividad_evaluativa_en_vivo import (
    ActividadEvaluativaEnVivo,
)
from src.actividad_evaluativa.entities.errors import (
    ConcurrenciaOptimistaError,
    SesionNoExiste,
    SesionYaIniciada,
    SinParticipantes,
)
from src.actividad_evaluativa.entities.eventos_en_vivo import SesionEnVivoIniciada
from src.actividad_evaluativa.entities.ports.canal_tiempo_real_port import CanalTiempoRealPort
from src.actividad_evaluativa.entities.ports.event_store_port import (
    EventoParaAlmacenar,
    EventStorePort,
)
from src.actividad_evaluativa.entities.ports.participantes_sesion_query_port import (
    ParticipantesSesionQueryPort,
)
from src.actividad_evaluativa.entities.ports.pregunta_consulta_port import PreguntaConsultaPort
from src.actividad_evaluativa.use_cases.pregunta_presentada import (
    mensaje_pregunta_presentada,
    payload_pregunta_presentada,
    tipo_de_pregunta,
)
from src.actividad_evaluativa.use_cases.verificar_autorizacion_comision import (
    VerificarAutorizacionComisionService,
)

AGGREGATE_TYPE_SESION = "ActividadEvaluativaEnVivo"


async def _persistir_inicio(
    event_store: EventStorePort, sesion_id: UUID, version: int, payload: dict[str, Any]
) -> None:
    """Guarda el evento `SesionEnVivoIniciada`, traduciendo la carrera optimista.

    Función libre para no sumar CBO a `IniciarSesionEnVivoUseCase` (`US-ADJ-57`).
    """
    try:
        await event_store.append(
            AGGREGATE_TYPE_SESION,
            sesion_id,
            version,
            [EventoParaAlmacenar(event_type="SesionEnVivoIniciada", payload=payload)],
        )
    except ConcurrenciaOptimistaError as exc:
        # Otro inicio concurrente ganó la carrera de insertar el evento — es exactamente el
        # caso "ya iniciada", no un error de infraestructura.
        raise SesionYaIniciada(sesion_id) from exc


class IniciarSesionEnVivoUseCase:
    """Orquesta el inicio de la sesión: transición a `EnCurso`, persistencia y broadcast."""

    def __init__(
        self,
        event_store: EventStorePort,
        pregunta_consulta: PreguntaConsultaPort,
        canal: CanalTiempoRealPort,
        participantes: ParticipantesSesionQueryPort,
        autorizacion: VerificarAutorizacionComisionService,
    ) -> None:
        """Recibe el event store, las consultas de preguntas/participantes y el canal.

        Recibe también el servicio de autorización por Comisión.
        """
        self._event_store = event_store
        self._pregunta_consulta = pregunta_consulta
        self._canal = canal
        self._participantes = participantes
        self._autorizacion = autorizacion

    async def execute(
        self, sesion_id: UUID, docente_id: UUID | None = None
    ) -> ActividadEvaluativaEnVivo:
        """Inicia la sesión y publica el enunciado de la primera pregunta a todos los conectados.

        Levanta `SesionNoExiste` si `sesion_id` no tiene stream, `ComisionNoAutorizada` (403)
        si `docente_id` no está asignado a la Comisión de la sesión (`US-ADJ-57`; `None` =
        Administrador, sin chequeo), y `SesionYaIniciada` si ya no está `EnEspera` — incluida
        la carrera de dos inicios simultáneos, que el chequeo optimista del event store
        resuelve dejando ganar a uno solo. Levanta además `SesionYaCancelada` si fue cancelada
        y `SinParticipantes` si no hay ningún Estudiante unido (INV-AEV-11, `US-ADJ-58`). El
        `tipo` de la pregunta se deriva de `opciones` (`None` = Verdadero/Falso, ver
        `ContenidoPregunta`); las opciones no viajan ni se persisten: las revela
        `MostrarOpcionesDeLaPregunta` (Iteración 2).

        Publica recién después de persistir; el canal es best-effort, así que un fallo de
        broadcast no revierte el inicio.
        """
        eventos = await self._event_store.load(AGGREGATE_TYPE_SESION, sesion_id)
        if not eventos:
            raise SesionNoExiste(sesion_id)

        sesion = ActividadEvaluativaEnVivo.reconstruir(eventos)
        await self._autorizacion.verificar_comision(docente_id, sesion.comision_id)

        sesion.iniciar()
        if not await self._participantes.listar(sesion_id):
            raise SinParticipantes(sesion_id)

        contenido = await self._pregunta_consulta.obtener_contenido(
            sesion.pregunta_actual().pregunta_id
        )
        evento = SesionEnVivoIniciada.desde_sesion(
            sesion, contenido.texto, tipo_de_pregunta(contenido)
        )

        await _persistir_inicio(
            self._event_store, sesion_id, len(eventos), payload_pregunta_presentada(evento)
        )

        await self._canal.publicar(sesion_id, mensaje_pregunta_presentada(evento))
        return sesion
