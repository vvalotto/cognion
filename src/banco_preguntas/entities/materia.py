"""Materia de la que se cargan preguntas — precondición del resto del BC (US-2.1.1)."""

from __future__ import annotations

from dataclasses import dataclass
from uuid import UUID, uuid4


@dataclass
class Materia:
    """Materia con nombre único en todo el sistema (INV-BP-00)."""

    id: UUID
    nombre: str

    @staticmethod
    def crear(nombre: str) -> Materia:
        """Crea una `Materia` nueva con id generado."""
        return Materia(id=uuid4(), nombre=nombre)
