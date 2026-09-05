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
        super().__init__(
            f"La comisión {comision_id} no pertenece a la materia {materia_id}."
        )
