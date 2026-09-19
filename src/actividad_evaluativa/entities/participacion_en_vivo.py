"""Aggregate `ParticipacionEnVivo` (`BC-actividad-evaluativa-modelo.md` §14)."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime
from uuid import UUID, uuid5

from src.actividad_evaluativa.entities.ports.event_store_port import EventoAlmacenado

_NAMESPACE_PARTICIPACION = UUID("5b7e0c1a-93d4-4f6e-a2b8-1c4d6e8f0a3b")


@dataclass
class ParticipacionEnVivo:
    """Participación de un Estudiante en una sesión en vivo — un aggregate por par.

    `id` determinístico (`id_para`) — el stream del event store se indexa por ese id, que sirve
    a la vez de mecanismo de idempotencia (INV-AEV-06): dos `UnirseASesionEnVivo` del mismo par
    resuelven al mismo stream. `respuestas` queda vacía en esta US; las agrega la Iteración 2.
    """

    id: UUID
    sesion_id: UUID
    estudiante_id: UUID
    unido_en: datetime = field(default_factory=lambda: datetime.now(UTC))
    respuestas: list[object] = field(default_factory=list)

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

    @staticmethod
    def reconstruir(eventos: list[EventoAlmacenado]) -> ParticipacionEnVivo:
        """Reconstruye la participación reproduciendo su stream (replay, `ADR-002`).

        Hoy el stream tiene un único evento posible, `EstudianteUnido`; las respuestas
        (Iteración 2) se sumarán como eventos posteriores.
        """
        payload = eventos[0].payload
        sesion_id = UUID(payload["sesion_id"])
        estudiante_id = UUID(payload["estudiante_id"])
        return ParticipacionEnVivo(
            id=ParticipacionEnVivo.id_para(sesion_id, estudiante_id),
            sesion_id=sesion_id,
            estudiante_id=estudiante_id,
            unido_en=datetime.fromisoformat(payload["unido_en"]),
        )
