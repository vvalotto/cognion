"""Fakes en memoria de los puertos exclusivos del modo en vivo, para tests unitarios."""

from __future__ import annotations

from datetime import datetime
from typing import Any
from uuid import UUID

from src.actividad_evaluativa.entities.ports.canal_tiempo_real_port import CanalTiempoRealPort
from src.actividad_evaluativa.entities.ports.comision_consulta_port import ComisionConsultaPort
from src.actividad_evaluativa.entities.ports.participantes_sesion_query_port import (
    ParticipanteResumen,
    ParticipantesSesionQueryPort,
)
from tests.unit.inc3._fakes import FakeEventStore


class FakeComisionConsultaPort(ComisionConsultaPort):
    """Consulta de comisiones en memoria — devuelve lo que se precarga en `materias`."""

    def __init__(self) -> None:
        """Inicializa el almacenamiento en memoria (`comision_id` → `materia_id`)."""
        self.materias: dict[UUID, UUID] = {}

    async def obtener_materia_id(self, comision_id: UUID) -> UUID | None:
        """Devuelve el `materia_id` precargado, o `None` si la comisión no fue precargada."""
        return self.materias.get(comision_id)


class FakeCanalTiempoReal(CanalTiempoRealPort):
    """Canal en vivo en memoria — registra cada mensaje publicado por sesión."""

    def __init__(self) -> None:
        """Inicializa la lista de publicaciones."""
        self.publicados: list[tuple[UUID, dict[str, Any]]] = []

    async def publicar(self, sesion_id: UUID, mensaje: dict[str, Any]) -> None:
        """Registra `(sesion_id, mensaje)` en `publicados`."""
        self.publicados.append((sesion_id, mensaje))


class FakeParticipantesSesionQueryPort(ParticipantesSesionQueryPort):
    """Read model en memoria — deriva los participantes de los eventos del `FakeEventStore`.

    Igual que el adapter real, lee los `EstudianteUnido` del event store en vez de mantener una
    proyección aparte.
    """

    def __init__(self, event_store: FakeEventStore) -> None:
        """Recibe el event store del que leer los streams de `ParticipacionEnVivo`."""
        self._event_store = event_store

    async def listar(self, sesion_id: UUID) -> list[ParticipanteResumen]:
        """Devuelve los participantes de `sesion_id` en orden de unión."""
        participantes = [
            ParticipanteResumen(
                estudiante_id=UUID(evento.payload["estudiante_id"]),
                unido_en=datetime.fromisoformat(evento.payload["unido_en"]),
            )
            for (aggregate_type, _), stream in self._event_store._streams.items()
            if aggregate_type == "ParticipacionEnVivo"
            for evento in stream
            if evento.event_type == "EstudianteUnido"
            and evento.payload["sesion_id"] == str(sesion_id)
        ]
        return sorted(participantes, key=lambda p: p.unido_en)
