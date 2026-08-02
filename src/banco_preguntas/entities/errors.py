"""Errores de dominio del BC Banco de Preguntas."""

from __future__ import annotations


class MateriaYaExiste(Exception):
    """Se intentó crear una materia con un nombre ya registrado (INV-BP-00)."""

    def __init__(self, nombre: str) -> None:
        """Guarda el nombre en conflicto y arma el mensaje de la excepción."""
        self.nombre = nombre
        super().__init__(f"La materia '{nombre}' ya existe.")
