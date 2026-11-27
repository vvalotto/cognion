"""Caso de uso: comisiones de una materia, acotadas a las del Docente que consulta."""

from __future__ import annotations

from uuid import UUID

from src.identidad.entities.comision import Comision
from src.identidad.entities.errors import MateriaNoAutorizada, MateriaNoExiste
from src.identidad.entities.ports.comision_query_port import ComisionQueryPort
from src.identidad.entities.ports.materia_port import MateriaPort


class ListarComisionesDeMateriaUseCase:
    """Lista las comisiones de una materia, validando que exista y que el Docente tenga alguna."""

    def __init__(self, comision_query: ComisionQueryPort, materia_port: MateriaPort) -> None:
        """Recibe el puerto de consulta de comisiones y el de materias."""
        self._comision_query = comision_query
        self._materia_port = materia_port

    async def execute(
        self,
        materia_id: UUID,
        incluir_inactivas: bool = False,
        docente_id: UUID | None = None,
    ) -> list[Comision]:
        """Devuelve las comisiones de `materia_id`; `MateriaNoExiste` si la materia no existe.

        `docente_id` (`US-ADJ-57`) acota el resultado a las comisiones propias del Docente que
        llama — `None` (Administrador) devuelve todas sin filtrar. `MateriaNoAutorizada` si el
        Docente no tiene ninguna comisión en esta materia.
        """
        if await self._materia_port.obtener(materia_id) is None:
            raise MateriaNoExiste(materia_id)
        comisiones = await self._comision_query.listar_comisiones_por_materia(
            materia_id, incluir_inactivas
        )
        if docente_id is None:
            return comisiones
        propias = [c for c in comisiones if docente_id in c.docentes_asignados]
        if not propias:
            raise MateriaNoAutorizada(materia_id)
        return propias
