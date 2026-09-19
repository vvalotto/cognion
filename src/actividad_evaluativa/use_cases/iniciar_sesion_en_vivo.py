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
)
from src.actividad_evaluativa.entities.eventos_en_vivo import SesionEnVivoIniciada
from src.actividad_evaluativa.entities.ports.canal_tiempo_real_port import CanalTiempoRealPort
from src.actividad_evaluativa.entities.ports.event_store_port import (
    EventoParaAlmacenar,
    EventStorePort,
)
from src.actividad_evaluativa.entities.ports.pregunta_consulta_port import PreguntaConsultaPort

AGGREGATE_TYPE_SESION = "ActividadEvaluativaEnVivo"


def _payload(evento: SesionEnVivoIniciada) -> dict[str, Any]:
    """Arma el payload persistido de `SesionEnVivoIniciada` (la pregunta, tal como se presentó)."""
    return {
        "sesion_id": str(evento.sesion_id),
        "pregunta_actual_indice": evento.pregunta_actual_indice,
        "pregunta": {
            "pregunta_id": str(evento.pregunta_id),
            "enunciado": evento.enunciado,
            "tipo": evento.tipo,
        },
        "ocurrido_en": evento.ocurrido_en.isoformat(),
    }


def _mensaje_pregunta(evento: SesionEnVivoIniciada) -> dict[str, Any]:
    """Arma el mensaje de broadcast: solo el enunciado de la pregunta actual, sin opciones (§16)."""
    return {
        "tipo": "pregunta_presentada",
        "pregunta_actual_indice": evento.pregunta_actual_indice,
        "pregunta": {
            "pregunta_id": str(evento.pregunta_id),
            "enunciado": evento.enunciado,
            "tipo": evento.tipo,
        },
    }


class IniciarSesionEnVivoUseCase:
    """Orquesta el inicio de la sesión: transición a `EnCurso`, persistencia y broadcast."""

    def __init__(
        self,
        event_store: EventStorePort,
        pregunta_consulta: PreguntaConsultaPort,
        canal: CanalTiempoRealPort,
    ) -> None:
        """Recibe el event store, la consulta de preguntas de Banco y el canal en vivo."""
        self._event_store = event_store
        self._pregunta_consulta = pregunta_consulta
        self._canal = canal

    async def execute(self, sesion_id: UUID) -> ActividadEvaluativaEnVivo:
        """Inicia la sesión y publica el enunciado de la primera pregunta a todos los conectados.

        Levanta `SesionNoExiste` si `sesion_id` no tiene stream y `SesionYaIniciada` si ya no
        está `EnEspera` — incluida la carrera de dos inicios simultáneos, que el chequeo
        optimista del event store resuelve dejando ganar a uno solo. El `tipo` de la pregunta se
        deriva de `opciones` (`None` = Verdadero/Falso, ver `ContenidoPregunta`); las opciones no
        viajan ni se persisten: las revela `MostrarOpcionesDeLaPregunta` (Iteración 2).

        Publica recién después de persistir; el canal es best-effort, así que un fallo de
        broadcast no revierte el inicio.
        """
        eventos = await self._event_store.load(AGGREGATE_TYPE_SESION, sesion_id)
        if not eventos:
            raise SesionNoExiste(sesion_id)

        sesion = ActividadEvaluativaEnVivo.reconstruir(eventos)
        sesion.iniciar()

        contenido = await self._pregunta_consulta.obtener_contenido(
            sesion.pregunta_actual().pregunta_id
        )
        tipo = "verdadero_falso" if contenido.opciones is None else "opcion_multiple"
        evento = SesionEnVivoIniciada.desde_sesion(sesion, contenido.texto, tipo)

        try:
            await self._event_store.append(
                AGGREGATE_TYPE_SESION,
                sesion_id,
                len(eventos),
                [EventoParaAlmacenar(event_type="SesionEnVivoIniciada", payload=_payload(evento))],
            )
        except ConcurrenciaOptimistaError as exc:
            # Otro inicio concurrente ganó la carrera de insertar el evento — es exactamente el
            # caso "ya iniciada", no un error de infraestructura.
            raise SesionYaIniciada(sesion_id) from exc

        await self._canal.publicar(sesion_id, _mensaje_pregunta(evento))
        return sesion
