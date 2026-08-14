"""Caso de uso: listado de materias con la cantidad de preguntas activas de cada una."""

from __future__ import annotations

from src.banco_preguntas.entities.banco import Banco
from src.banco_preguntas.entities.materia import Materia
from src.banco_preguntas.entities.ports.banco_repository_port import BancoRepositoryPort
from src.banco_preguntas.entities.ports.materia_repository_port import MateriaRepositoryPort
from src.banco_preguntas.entities.ports.pregunta_repository_port import PreguntaRepositoryPort


class ListarMateriasUseCase:
    """Lista materias junto con su banco y la cantidad de preguntas activas asociadas."""

    def __init__(
        self,
        materia_repositorio: MateriaRepositoryPort,
        banco_repositorio: BancoRepositoryPort,
        pregunta_repositorio: PreguntaRepositoryPort,
    ) -> None:
        """Recibe los repositorios de materias, bancos y preguntas a usar."""
        self._materia_repositorio = materia_repositorio
        self._banco_repositorio = banco_repositorio
        self._pregunta_repositorio = pregunta_repositorio

    async def execute(self) -> list[tuple[Materia, Banco, int]]:
        """Devuelve cada materia con su banco y la cantidad de preguntas `activa = true`.

        Reutiliza `PreguntaRepositoryPort.filtrar()` (`US-2.1.7`) para el conteo, sin agregar
        un método dedicado a ese puerto.
        """
        materias = await self._materia_repositorio.listar()

        resultado: list[tuple[Materia, Banco, int]] = []
        for materia in materias:
            banco = await self._banco_repositorio.obtener_por_materia_id(materia.id)
            assert banco is not None, f"Materia {materia.id} sin Banco asociado (INV-BP-01)"
            preguntas_activas = await self._pregunta_repositorio.filtrar(banco.id)
            resultado.append((materia, banco, len(preguntas_activas)))

        return resultado
