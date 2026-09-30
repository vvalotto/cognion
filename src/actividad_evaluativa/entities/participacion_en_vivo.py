"""Aggregate `ParticipacionEnVivo` (`BC-actividad-evaluativa-modelo.md` §14)."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any
from uuid import UUID, uuid5

from src.actividad_evaluativa.entities.errors import RespuestaYaRegistrada
from src.actividad_evaluativa.entities.ports.event_store_port import EventoAlmacenado

_NAMESPACE_PARTICIPACION = UUID("5b7e0c1a-93d4-4f6e-a2b8-1c4d6e8f0a3b")


@dataclass(frozen=True)
class RespuestaEnVivo:
    """Respuesta de un Estudiante a una pregunta de la sesión en vivo — inmutable (§14).

    `contenido` tiene el mismo shape que `Respuesta.contenido` (`{opcion_indice}` o `{valor}`);
    `tiempo_respuesta_segundos` lo mide el servidor, nunca el cliente.
    """

    pregunta_id: UUID
    contenido: dict[str, Any]
    es_correcta: bool
    tiempo_respuesta_segundos: float
    puntaje: int


@dataclass
class ParticipacionEnVivo:
    """Participación de un Estudiante en una sesión en vivo — un aggregate por par.

    `id` determinístico (`id_para`) — el stream del event store se indexa por ese id, que sirve
    a la vez de mecanismo de idempotencia (INV-AEV-06): dos `UnirseASesionEnVivo` del mismo par
    resuelven al mismo stream. `respuestas` guarda una `RespuestaEnVivo` por pregunta (INV-AEV-07).
    """

    id: UUID
    sesion_id: UUID
    estudiante_id: UUID
    unido_en: datetime = field(default_factory=lambda: datetime.now(UTC))
    respuestas: list[RespuestaEnVivo] = field(default_factory=list)

    @staticmethod
    def id_para(sesion_id: UUID, estudiante_id: UUID) -> UUID:
        """Deriva el id determinístico del par `(sesion_id, estudiante_id)` (INV-AEV-06)."""
        return uuid5(_NAMESPACE_PARTICIPACION, f"{sesion_id}:{estudiante_id}")

    @staticmethod
    def unirse(sesion_id: UUID, estudiante_id: UUID) -> ParticipacionEnVivo:
        """Crea la participación de `estudiante_id` en `sesion_id`.

        Sin validación propia: que la sesión exista y no esté `Finalizada`, y la idempotencia
        (no crear una segunda), son responsabilidad del Use Case, que necesita el event store.
        """
        return ParticipacionEnVivo(
            id=ParticipacionEnVivo.id_para(sesion_id, estudiante_id),
            sesion_id=sesion_id,
            estudiante_id=estudiante_id,
        )

    @property
    def puntaje_acumulado(self) -> int:
        """Suma el puntaje de todas las respuestas de la participación."""
        return sum(respuesta.puntaje for respuesta in self.respuestas)

    def validar_para_responder(self, pregunta_id: UUID) -> None:
        """Rechaza con `RespuestaYaRegistrada` si ya respondió `pregunta_id` (INV-AEV-07)."""
        if any(respuesta.pregunta_id == pregunta_id for respuesta in self.respuestas):
            raise RespuestaYaRegistrada(self.sesion_id, pregunta_id)

    def responder(
        self,
        pregunta_id: UUID,
        contenido: dict[str, Any],
        es_correcta: bool,
        tiempo_respuesta_segundos: float,
        puntaje: int,
    ) -> RespuestaEnVivo:
        """Registra la respuesta a `pregunta_id` — un solo intento por pregunta (INV-AEV-07)."""
        self.validar_para_responder(pregunta_id)
        respuesta = RespuestaEnVivo(
            pregunta_id=pregunta_id,
            contenido=contenido,
            es_correcta=es_correcta,
            tiempo_respuesta_segundos=tiempo_respuesta_segundos,
            puntaje=puntaje,
        )
        self.respuestas.append(respuesta)
        return respuesta

    @staticmethod
    def reconstruir(eventos: list[EventoAlmacenado]) -> ParticipacionEnVivo:
        """Reconstruye la participación reproduciendo su stream (replay, `ADR-002`).

        El primer evento es `EstudianteUnido` (arma la base); los siguientes, de tipo
        `RespuestaEnVivoRegistrada`, suman una `RespuestaEnVivo` cada uno.
        """
        payload = eventos[0].payload
        sesion_id = UUID(payload["sesion_id"])
        estudiante_id = UUID(payload["estudiante_id"])
        participacion = ParticipacionEnVivo(
            id=ParticipacionEnVivo.id_para(sesion_id, estudiante_id),
            sesion_id=sesion_id,
            estudiante_id=estudiante_id,
            unido_en=datetime.fromisoformat(payload["unido_en"]),
        )
        for evento in eventos[1:]:
            if evento.event_type == "RespuestaEnVivoRegistrada":
                participacion.respuestas.append(
                    RespuestaEnVivo(
                        pregunta_id=UUID(evento.payload["pregunta_id"]),
                        contenido=evento.payload["contenido"],
                        es_correcta=evento.payload["es_correcta"],
                        tiempo_respuesta_segundos=evento.payload["tiempo_respuesta_segundos"],
                        puntaje=evento.payload["puntaje"],
                    )
                )
        return participacion
