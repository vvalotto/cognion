from __future__ import annotations

from uuid import UUID

from src.identidad.entities.comision import Comision
from src.identidad.entities.errors import ComisionNoExiste, UsuarioNoEsDocente
from src.identidad.entities.eventos import DocenteAsignado
from src.identidad.entities.ports.comision_repository_port import ComisionRepositoryPort
from src.identidad.entities.ports.usuario_repository_port import UsuarioRepositoryPort
from src.identidad.entities.usuario import Docente


class AsignarDocenteAComisionUseCase:
    def __init__(
        self,
        comision_repositorio: ComisionRepositoryPort,
        usuario_repositorio: UsuarioRepositoryPort,
    ) -> None:
        self._comision_repositorio = comision_repositorio
        self._usuario_repositorio = usuario_repositorio

    async def execute(
        self, comision_id: UUID, docente_id: UUID
    ) -> tuple[Comision, DocenteAsignado]:
        usuario = await self._usuario_repositorio.obtener_por_id(docente_id)
        if usuario is None or not isinstance(usuario.perfil, Docente):
            raise UsuarioNoEsDocente(docente_id)

        comision = await self._comision_repositorio.obtener_por_id(comision_id)
        if comision is None:
            raise ComisionNoExiste(comision_id)

        comision.asignar_docente(docente_id)
        await self._comision_repositorio.actualizar(comision)

        evento = DocenteAsignado(comision_id=comision.id, docente_id=docente_id)
        return comision, evento
