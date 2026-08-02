"""Caso de uso: alta de una materia y su banco de preguntas asociado."""

from __future__ import annotations

from src.banco_preguntas.entities.banco import Banco
from src.banco_preguntas.entities.errors import MateriaYaExiste
from src.banco_preguntas.entities.eventos import BancoCreado, MateriaCreada
from src.banco_preguntas.entities.materia import Materia
from src.banco_preguntas.entities.ports.banco_repository_port import BancoRepositoryPort
from src.banco_preguntas.entities.ports.materia_repository_port import MateriaRepositoryPort


class CrearMateriaUseCase:
    """Registra una materia nueva y crea su banco en la misma operación (INV-BP-00, INV-BP-01)."""

    def __init__(
        self,
        materia_repositorio: MateriaRepositoryPort,
        banco_repositorio: BancoRepositoryPort,
    ) -> None:
        """Recibe los repositorios de materias y bancos a usar."""
        self._materia_repositorio = materia_repositorio
        self._banco_repositorio = banco_repositorio

    async def execute(
        self, nombre: str
    ) -> tuple[Materia, Banco, MateriaCreada, BancoCreado]:
        """Crea y persiste `Materia` + `Banco`; levanta `MateriaYaExiste` si el nombre existe."""
        existente = await self._materia_repositorio.obtener_por_nombre(nombre)
        if existente is not None:
            raise MateriaYaExiste(nombre)

        materia = Materia.crear(nombre)
        await self._materia_repositorio.guardar(materia)

        banco = Banco.crear(materia.id)
        await self._banco_repositorio.guardar(banco)

        evento_materia = MateriaCreada(materia_id=materia.id, nombre=materia.nombre)
        evento_banco = BancoCreado(banco_id=banco.id, materia_id=materia.id)
        return materia, banco, evento_materia, evento_banco
