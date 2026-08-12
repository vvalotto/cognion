"""Adaptador de `MateriaPort` — llamada in-process a BC Banco de Preguntas.

Mismo criterio que `ADR-006` (integración directa entre BCs documentada como acoplamiento
consciente en vez de indirección prematura): vive en `frameworks/` de Identidad, nunca en
`entities/` ni `use_cases/`, y es el único punto de Identidad que importa `src.banco_preguntas`.
"""

from __future__ import annotations

from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from src.banco_preguntas.interface_adapters.gateways.materia_repository import (
    SQLAlchemyMateriaRepository,
)
from src.banco_preguntas.use_cases.obtener_materia import ObtenerMateriaUseCase
from src.identidad.entities.ports.materia_port import MateriaDTO, MateriaPort


class MateriaPortInProcess(MateriaPort):
    """Implementa `MateriaPort` invocando `ObtenerMateriaUseCase` en el mismo proceso."""

    def __init__(self, session: AsyncSession) -> None:
        """Recibe la sesión async de Identidad, compartida con el repositorio de Materia."""
        self._obtener_materia = ObtenerMateriaUseCase(SQLAlchemyMateriaRepository(session))

    async def obtener(self, materia_id: UUID) -> MateriaDTO | None:
        """Busca la materia por id, o `None` si no existe."""
        materia = await self._obtener_materia.execute(materia_id)
        if materia is None:
            return None
        return MateriaDTO(id=materia.id, nombre=materia.nombre)
