"""Errores de dominio propios del BC Analytics.

Primer archivo de errores del BC — mismo criterio que `src/actividad_evaluativa/entities/errors.py`:
excepciones puras, sin dependencia de FastAPI, que el router mapea a status codes HTTP.
"""

from __future__ import annotations

from uuid import UUID

from src.shared.entities.errors import NoAutorizado, NoEncontrado, ReglaViolada


class ComisionNoPerteneceAMateria(ReglaViolada):
    """La comisión indicada para acotar el agregado no pertenece a la materia consultada."""

    def __init__(self, comision_id: UUID, materia_id: UUID) -> None:
        """Registra los ids involucrados para el mensaje de error (US-4.2.4)."""
        super().__init__(f"La comisión {comision_id} no pertenece a la materia {materia_id}.")


class ActividadNoExiste(NoEncontrado):
    """No existe ninguna `ActividadEvaluativaPeriodoAbierto` con el id consultado (US-ADJ-47)."""

    def __init__(self, actividad_id: UUID) -> None:
        """Registra el id de la actividad para el mensaje de error."""
        super().__init__(f"No existe una actividad con id {actividad_id}.")


class EstudianteNoExiste(NoEncontrado):
    """No existe un Estudiante con el id consultado por el Docente (`US-4.2.1`, `US-ADJ-45`)."""

    def __init__(self, estudiante_id: UUID) -> None:
        """Registra el id del estudiante para el mensaje de error."""
        super().__init__(f"No existe un Estudiante con id {estudiante_id}.")


class MateriaNoAutorizada(NoAutorizado):
    """El Docente solicitante no tiene ninguna Comisión asignada en esta materia (`US-ADJ-57`).

    Nivel de autorización de los informes que agregan toda la materia, o que reciben
    `comision_id` en `None` — mismo criterio que `MateriaNoAutorizada` de Actividad Evaluativa
    y Banco de Preguntas.
    """

    def __init__(self, materia_id: UUID) -> None:
        """Guarda el id de la materia ajena y arma el mensaje de la excepción."""
        self.materia_id = materia_id
        super().__init__(f"No tenés ninguna Comisión asignada en la materia '{materia_id}'.")


class ComisionNoAutorizada(NoAutorizado):
    """El Docente solicitante no está asignado a la Comisión consultada (`US-ADJ-57`).

    Nivel de autorización de los informes que acotan a una `comision_id` concreta.
    """

    def __init__(self, comision_id: UUID) -> None:
        """Guarda el id de la comisión ajena y arma el mensaje de la excepción."""
        self.comision_id = comision_id
        super().__init__(f"No estás asignado a la comisión '{comision_id}'.")
