"""Banco de preguntas de una materia — 1:1 con `Materia` (INV-BP-01)."""

from __future__ import annotations

from dataclasses import dataclass
from uuid import UUID, uuid4


@dataclass
class Banco:
    """Banco de preguntas asociado a una única `Materia`."""

    id: UUID
    materia_id: UUID

    @staticmethod
    def crear(materia_id: UUID) -> Banco:
        """Crea un `Banco` nuevo para la materia indicada."""
        return Banco(id=uuid4(), materia_id=materia_id)
