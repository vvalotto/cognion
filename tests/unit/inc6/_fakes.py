"""Fakes en memoria de los puertos exclusivos del modo en vivo, para tests unitarios."""

from __future__ import annotations

from uuid import UUID

from src.actividad_evaluativa.entities.ports.comision_consulta_port import ComisionConsultaPort


class FakeComisionConsultaPort(ComisionConsultaPort):
    """Consulta de comisiones en memoria — devuelve lo que se precarga en `materias`."""

    def __init__(self) -> None:
        """Inicializa el almacenamiento en memoria (`comision_id` → `materia_id`)."""
        self.materias: dict[UUID, UUID] = {}

    async def obtener_materia_id(self, comision_id: UUID) -> UUID | None:
        """Devuelve el `materia_id` precargado, o `None` si la comisión no fue precargada."""
        return self.materias.get(comision_id)
