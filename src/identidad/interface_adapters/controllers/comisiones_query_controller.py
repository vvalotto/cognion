"""Controller de consultas de solo lectura sobre comisiones (`US-4.2.2`).

Separado de `ComisionesController` (comandos: crear comisión, asignar docente) por
responsabilidad command/query, mismo criterio que separa `CuentasController` de
`UsuariosController` (`US-2.2.2`). Desde `US-12.2.4` solo delega y presenta: la existencia y la
autorización del Docente las resuelven casos de uso.
"""

from __future__ import annotations

from uuid import UUID

from src.identidad.interface_adapters.presenters.identidad_presenter import (
    ComisionResumenSalida,
    ComisionSalida,
    EstudianteResumenSalida,
    presentar_comision,
    presentar_comisiones_resumen,
    presentar_estudiantes,
)
from src.identidad.use_cases.listar_comisiones_de_materia import ListarComisionesDeMateriaUseCase
from src.identidad.use_cases.listar_estudiantes_de_comision import (
    ListarEstudiantesDeComisionUseCase,
)
from src.identidad.use_cases.obtener_comision import ObtenerComisionUseCase


class ComisionesQueryController:
    """Adapta requests HTTP a las consultas de solo lectura sobre comisiones."""

    def __init__(
        self,
        listar_comisiones_de_materia: ListarComisionesDeMateriaUseCase,
        listar_estudiantes_de_comision: ListarEstudiantesDeComisionUseCase,
        obtener_comision: ObtenerComisionUseCase,
    ) -> None:
        """Recibe los tres casos de uso de consulta de comisiones."""
        self._listar_comisiones_de_materia = listar_comisiones_de_materia
        self._listar_estudiantes_de_comision = listar_estudiantes_de_comision
        self._obtener_comision = obtener_comision

    async def listar_comisiones_por_materia(
        self,
        materia_id: UUID,
        incluir_inactivas: bool = False,
        docente_id: UUID | None = None,
    ) -> list[ComisionResumenSalida]:
        """Lista las comisiones de una materia; `docente_id` acota a las del Docente (`US-ADJ-57`)."""
        comisiones = await self._listar_comisiones_de_materia.execute(
            materia_id, incluir_inactivas, docente_id
        )
        return presentar_comisiones_resumen(comisiones)

    async def listar_estudiantes(
        self, comision_id: UUID, docente_id: UUID | None = None
    ) -> list[EstudianteResumenSalida]:
        """Lista los estudiantes de una comisión (`ComisionNoAutorizada` si el Docente no es suyo)."""
        estudiantes = await self._listar_estudiantes_de_comision.execute(comision_id, docente_id)
        return presentar_estudiantes(estudiantes)

    async def obtener_comision(
        self, comision_id: UUID, docente_id: UUID | None = None
    ) -> ComisionSalida:
        """Devuelve una comisión puntual (`US-ADJ-25`), autorizada para el Docente (`US-ADJ-57`)."""
        return presentar_comision(await self._obtener_comision.execute(comision_id, docente_id))
