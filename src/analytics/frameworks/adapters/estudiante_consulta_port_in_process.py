"""Adaptador de `EstudianteConsultaPort` — llamada in-process a BC Identidad.

Mismo criterio de acoplamiento consciente (`ADR-006`) que
`src/actividad_evaluativa/frameworks/adapters/estudiante_consulta_port_in_process.py`: vive en
`frameworks/`, nunca en `entities/` ni `use_cases/`, y es el único punto de Analytics que
importa `src.identidad` (`US-4.2.1`).
"""

from __future__ import annotations

from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from src.analytics.entities.ports.estudiante_consulta_port import EstudianteConsultaPort
from src.identidad.interface_adapters.gateways.usuario_repository import (
    SQLAlchemyUsuarioRepository,
)
from src.shared.entities.tipo_perfil import TipoPerfil


class EstudianteConsultaPortInProcess(EstudianteConsultaPort):
    """Implementa `EstudianteConsultaPort` invocando el repositorio de `Usuario` in-process."""

    def __init__(self, session: AsyncSession) -> None:
        """Recibe la sesión async compartida con el repositorio de `Usuario`."""
        self._usuario_repositorio = SQLAlchemyUsuarioRepository(session)

    async def existe(self, estudiante_id: UUID) -> bool:
        """Indica si `estudiante_id` es un `Usuario` existente con rol Estudiante."""
        usuario = await self._usuario_repositorio.obtener_por_id(estudiante_id)
        if usuario is None:
            return False
        return usuario.tipo_perfil is TipoPerfil.ESTUDIANTE
