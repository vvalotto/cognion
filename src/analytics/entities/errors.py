"""Errores de dominio propios del BC Analytics.

Primer archivo de errores del BC — mismo criterio que `src/actividad_evaluativa/entities/errors.py`:
excepciones puras, sin dependencia de FastAPI, que el router mapea a status codes HTTP.
"""

from __future__ import annotations

from uuid import UUID


class ComisionNoPerteneceAMateria(Exception):
    """La comisión indicada para acotar el agregado no pertenece a la materia consultada."""

    def __init__(self, comision_id: UUID, materia_id: UUID) -> None:
        """Registra los ids involucrados para el mensaje de error (US-4.2.4)."""
        super().__init__(f"La comisión {comision_id} no pertenece a la materia {materia_id}.")


class ActividadNoExiste(Exception):
    """No existe ninguna `ActividadEvaluativaPeriodoAbierto` con el id consultado (US-ADJ-47)."""

    def __init__(self, actividad_id: UUID) -> None:
        """Registra el id de la actividad para el mensaje de error."""
        super().__init__(f"No existe una actividad con id {actividad_id}.")


class MateriaNoAutorizada(Exception):
    """El Docente solicitante no tiene ninguna Comisión asignada en esta materia (`US-ADJ-57`).

    Nivel de autorización de los informes que agregan toda la materia, o que reciben
    `comision_id` en `None` — mismo criterio que `MateriaNoAutorizada` de Actividad Evaluativa
    y Banco de Preguntas.
    """

    def __init__(self, materia_id: UUID) -> None:
        """Guarda el id de la materia ajena y arma el mensaje de la excepción."""
        self.materia_id = materia_id
        super().__init__(f"No tenés ninguna Comisión asignada en la materia '{materia_id}'.")


class ComisionNoAutorizada(Exception):
    """El Docente solicitante no está asignado a la Comisión consultada (`US-ADJ-57`).

    Nivel de autorización de los informes que acotan a una `comision_id` concreta.
    """

    def __init__(self, comision_id: UUID) -> None:
        """Guarda el id de la comisión ajena y arma el mensaje de la excepción."""
        self.comision_id = comision_id
        super().__init__(f"No estás asignado a la comisión '{comision_id}'.")
