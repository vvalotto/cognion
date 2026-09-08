"""Materia de la que se cargan preguntas — precondición del resto del BC (US-2.1.1)."""

from __future__ import annotations

from dataclasses import dataclass
from uuid import UUID, uuid4


@dataclass
class Materia:
    """Materia con nombre único en todo el sistema (INV-BP-00)."""

    id: UUID
    nombre: str
    activa: bool = True

    @staticmethod
    def crear(nombre: str) -> Materia:
        """Crea una `Materia` nueva con id generado."""
        return Materia(id=uuid4(), nombre=nombre)

    def renombrar(self, nombre: str) -> None:
        """Corrige el nombre de la materia (típicamente, un error de tipeo al crearla).

        La unicidad del nombre nuevo la valida el caso de uso, que sí tiene acceso al
        repositorio (INV-BP-00).
        """
        self.nombre = nombre

    def deshabilitar(self) -> None:
        """Da de baja lógica la materia (tiene preguntas o comisiones, no se puede borrar)."""
        self.activa = False
