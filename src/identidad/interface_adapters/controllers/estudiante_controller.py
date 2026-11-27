"""Controller de la API para operaciones de autoservicio del Estudiante."""

from __future__ import annotations

from uuid import UUID

from src.identidad.interface_adapters.presenters.identidad_presenter import (
    MateriaEstudianteSalida,
    presentar_materias_estudiante,
)
from src.identidad.use_cases.listar_materias_del_estudiante import (
    ListarMateriasDelEstudianteUseCase,
)


class EstudianteController:
    """Adapta requests HTTP a los casos de uso de autoservicio del Estudiante."""

    def __init__(self, listar_materias: ListarMateriasDelEstudianteUseCase) -> None:
        """Recibe el caso de uso de listado de materias del Estudiante."""
        self._listar_materias = listar_materias

    async def listar_mis_materias(self, estudiante_id: UUID) -> list[MateriaEstudianteSalida]:
        """Delega la resolución de la materia de la comisión en el caso de uso correspondiente."""
        return presentar_materias_estudiante(await self._listar_materias.execute(estudiante_id))
