"""Errores de dominio del BC Banco de Preguntas."""

from __future__ import annotations


class MateriaYaExiste(Exception):
    """Se intentó crear una materia con un nombre ya registrado (INV-BP-00)."""

    def __init__(self, nombre: str) -> None:
        """Guarda el nombre en conflicto y arma el mensaje de la excepción."""
        self.nombre = nombre
        super().__init__(f"La materia '{nombre}' ya existe.")


class BancoNoExiste(Exception):
    """Se referenció un `banco_id` que no corresponde a ningún `Banco` existente."""

    def __init__(self, banco_id: object) -> None:
        """Guarda el id inexistente y arma el mensaje de la excepción."""
        self.banco_id = banco_id
        super().__init__(f"El banco '{banco_id}' no existe.")


class OpcionesInvalidas(Exception):
    """Las opciones de una pregunta de opción múltiple violan INV-BP-02 o INV-BP-03."""


class PreguntaNoExiste(Exception):
    """Se referenció un `pregunta_id` que no corresponde a ninguna `PreguntaPlantilla` existente."""

    def __init__(self, pregunta_id: object) -> None:
        """Guarda el id inexistente y arma el mensaje de la excepción."""
        self.pregunta_id = pregunta_id
        super().__init__(f"La pregunta '{pregunta_id}' no existe.")


class PreguntaInactiva(Exception):
    """Se intentó editar una `PreguntaPlantilla` con `activa = false`."""

    def __init__(self, pregunta_id: object) -> None:
        """Guarda el id de la pregunta inactiva y arma el mensaje de la excepción."""
        self.pregunta_id = pregunta_id
        super().__init__(f"La pregunta '{pregunta_id}' está inactiva y no puede editarse.")


class PreguntaYaEliminada(Exception):
    """Se intentó eliminar una `PreguntaPlantilla` que ya tiene `activa = false`."""

    def __init__(self, pregunta_id: object) -> None:
        """Guarda el id de la pregunta ya eliminada y arma el mensaje de la excepción."""
        self.pregunta_id = pregunta_id
        super().__init__(f"La pregunta '{pregunta_id}' ya fue eliminada.")
