"""Caso de uso: materia de la comisión del Estudiante autenticado."""

from __future__ import annotations

from dataclasses import dataclass
from uuid import UUID

from src.identidad.entities.errors import ComisionNoExiste, MateriaNoExiste, UsuarioNoExiste
from src.identidad.entities.ports.comision_repository_port import ComisionRepositoryPort
from src.identidad.entities.ports.materia_port import MateriaPort
from src.identidad.entities.ports.usuario_repository_port import UsuarioRepositoryPort
from src.identidad.entities.usuario import Estudiante


@dataclass(frozen=True)
class MateriaEstudianteResumen:
    """Materia de la comisión del Estudiante, con el nombre resuelto vía `MateriaPort`."""

    id: UUID
    nombre: str


class ListarMateriasDelEstudianteUseCase:
    """Resuelve la materia de la comisión del Estudiante autenticado (RF-11)."""

    def __init__(
        self,
        usuario_repositorio: UsuarioRepositoryPort,
        comision_repositorio: ComisionRepositoryPort,
        materia_port: MateriaPort,
    ) -> None:
        """Recibe los repositorios de usuarios/comisiones y el puerto de materias a usar."""
        self._usuario_repositorio = usuario_repositorio
        self._comision_repositorio = comision_repositorio
        self._materia_port = materia_port

    async def execute(self, estudiante_id: UUID) -> list[MateriaEstudianteResumen]:
        """Devuelve la materia de la comisión del Estudiante, en una lista de a lo sumo un ítem.

        Lanza `UsuarioNoExiste`/`ComisionNoExiste`/`MateriaNoExiste` si alguna referencia
        resultara inválida — no debería ocurrir dado INV-ID-05, pero cada repositorio/puerto
        puede devolver `None`.
        """
        usuario = await self._usuario_repositorio.obtener_por_id(estudiante_id)
        if usuario is None:
            raise UsuarioNoExiste(estudiante_id)
        assert isinstance(usuario.perfil, Estudiante)

        comision = await self._comision_repositorio.obtener_por_id(usuario.perfil.comision_id)
        if comision is None:
            raise ComisionNoExiste(usuario.perfil.comision_id)

        materia = await self._materia_port.obtener(comision.materia_id)
        if materia is None:
            raise MateriaNoExiste(comision.materia_id)

        return [MateriaEstudianteResumen(id=materia.id, nombre=materia.nombre)]
