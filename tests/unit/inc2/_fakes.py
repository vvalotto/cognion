"""Fakes en memoria de los puertos del BC Banco de Preguntas, para tests unitarios."""

from __future__ import annotations

from uuid import UUID

from src.banco_preguntas.entities.banco import Banco
from src.banco_preguntas.entities.materia import Materia
from src.banco_preguntas.entities.ports.banco_repository_port import BancoRepositoryPort
from src.banco_preguntas.entities.ports.materia_repository_port import MateriaRepositoryPort
from src.banco_preguntas.entities.ports.pregunta_repository_port import PreguntaRepositoryPort
from src.banco_preguntas.entities.pregunta_plantilla import (
    PreguntaPlantillaOpcionMultiple,
    PreguntaPlantillaVerdaderoFalso,
)


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

    async def obtener_por_id(self, materia_id: UUID) -> Materia | None:
        """Busca una materia por id, o `None` si no existe."""
        return self.materias.get(materia_id)


class FakeBancoRepository(BancoRepositoryPort):
    """Repositorio de bancos en memoria."""

    def __init__(self) -> None:
        """Inicializa el almacenamiento en memoria."""
        self.bancos: dict[UUID, Banco] = {}

    async def guardar(self, banco: Banco) -> None:
        """Guarda un banco nuevo."""
        self.bancos[banco.id] = banco

    async def obtener_por_id(self, banco_id: UUID) -> Banco | None:
        """Busca un banco por id, o `None` si no existe."""
        return self.bancos.get(banco_id)


class FakePreguntaRepository(PreguntaRepositoryPort):
    """Repositorio de preguntas en memoria."""

    def __init__(self) -> None:
        """Inicializa el almacenamiento en memoria."""
        self.preguntas: dict[
            UUID, PreguntaPlantillaOpcionMultiple | PreguntaPlantillaVerdaderoFalso
        ] = {}

    async def guardar(
        self, pregunta: PreguntaPlantillaOpcionMultiple | PreguntaPlantillaVerdaderoFalso
    ) -> None:
        """Guarda una pregunta nueva."""
        self.preguntas[pregunta.id] = pregunta

    async def obtener_por_id(
        self, pregunta_id: UUID
    ) -> PreguntaPlantillaOpcionMultiple | PreguntaPlantillaVerdaderoFalso | None:
        """Busca una pregunta por id, o `None` si no existe."""
        return self.preguntas.get(pregunta_id)

    async def actualizar(
        self, pregunta: PreguntaPlantillaOpcionMultiple | PreguntaPlantillaVerdaderoFalso
    ) -> None:
        """Persiste los cambios de una pregunta ya existente."""
        self.preguntas[pregunta.id] = pregunta
