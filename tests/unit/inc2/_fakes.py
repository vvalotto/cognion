"""Fakes en memoria de los puertos del BC Banco de Preguntas, para tests unitarios."""

from __future__ import annotations

from uuid import UUID

from src.banco_preguntas.entities.banco import Banco
from src.banco_preguntas.entities.materia import Materia
from src.banco_preguntas.entities.ports.banco_repository_port import BancoRepositoryPort
from src.banco_preguntas.entities.ports.materia_repository_port import MateriaRepositoryPort


class FakeMateriaRepository(MateriaRepositoryPort):
    """Repositorio de materias en memoria."""

    def __init__(self) -> None:
        """Inicializa el almacenamiento en memoria."""
        self.materias: dict[UUID, Materia] = {}

    async def guardar(self, materia: Materia) -> None:
        """Guarda una materia nueva."""
        self.materias[materia.id] = materia

    async def obtener_por_nombre(self, nombre: str) -> Materia | None:
        """Busca una materia por nombre, o `None` si no existe."""
        for materia in self.materias.values():
            if materia.nombre == nombre:
                return materia
        return None


class FakeBancoRepository(BancoRepositoryPort):
    """Repositorio de bancos en memoria."""

    def __init__(self) -> None:
        """Inicializa el almacenamiento en memoria."""
        self.bancos: dict[UUID, Banco] = {}

    async def guardar(self, banco: Banco) -> None:
        """Guarda un banco nuevo."""
        self.bancos[banco.id] = banco
