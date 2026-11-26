"""Errores de dominio del BC Banco de Preguntas."""

from __future__ import annotations

from src.shared.entities.errors import Conflicto, NoAutorizado, NoEncontrado, ReglaViolada


class MateriaYaExiste(Conflicto):
    """Se intentó crear una materia con un nombre ya registrado (INV-BP-00)."""

    def __init__(self, nombre: str) -> None:
        """Guarda el nombre en conflicto y arma el mensaje de la excepción."""
        self.nombre = nombre
        super().__init__(f"La materia '{nombre}' ya existe.")


class MateriaNoExiste(NoEncontrado):
    """Se referenció un `materia_id` que no corresponde a ninguna `Materia` existente."""

    def __init__(self, materia_id: object) -> None:
        """Guarda el id inexistente y arma el mensaje de la excepción."""
        self.materia_id = materia_id
        super().__init__(f"La materia '{materia_id}' no existe.")


class BancoNoExiste(NoEncontrado):
    """Se referenció un `banco_id` que no corresponde a ningún `Banco` existente."""

    def __init__(self, banco_id: object) -> None:
        """Guarda el id inexistente y arma el mensaje de la excepción."""
        self.banco_id = banco_id
        super().__init__(f"El banco '{banco_id}' no existe.")


class MateriaNoAutorizada(NoAutorizado):
    """El Docente solicitante no tiene ninguna Comisión asignada en esta materia (`US-ADJ-57`)."""

    def __init__(self, materia_id: object) -> None:
        """Guarda el id de la materia ajena y arma el mensaje de la excepción."""
        self.materia_id = materia_id
        super().__init__(f"No tenés ninguna Comisión asignada en la materia '{materia_id}'.")


class OpcionesInvalidas(ReglaViolada):
    """Las opciones de una pregunta de opción múltiple violan INV-BP-02 o INV-BP-03."""


class PreguntaNoExiste(NoEncontrado):
    """Se referenció un `pregunta_id` que no corresponde a ninguna `PreguntaPlantilla` existente."""

    def __init__(self, pregunta_id: object) -> None:
        """Guarda el id inexistente y arma el mensaje de la excepción."""
        self.pregunta_id = pregunta_id
        super().__init__(f"La pregunta '{pregunta_id}' no existe.")


class PreguntaInactiva(Conflicto):
    """Se intentó editar una `PreguntaPlantilla` con `activa = false`."""

    def __init__(self, pregunta_id: object) -> None:
        """Guarda el id de la pregunta inactiva y arma el mensaje de la excepción."""
        self.pregunta_id = pregunta_id
        super().__init__(f"La pregunta '{pregunta_id}' está inactiva y no puede editarse.")


class PreguntaYaEliminada(Conflicto):
    """Se intentó eliminar una `PreguntaPlantilla` que ya tiene `activa = false`."""

    def __init__(self, pregunta_id: object) -> None:
        """Guarda el id de la pregunta ya eliminada y arma el mensaje de la excepción."""
        self.pregunta_id = pregunta_id
        super().__init__(f"La pregunta '{pregunta_id}' ya fue eliminada.")
