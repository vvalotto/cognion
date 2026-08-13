"""Caso de uso: filtrado del banco de preguntas de una materia por metadatos."""

from __future__ import annotations

from uuid import UUID

from src.banco_preguntas.entities.errors import BancoNoExiste
from src.banco_preguntas.entities.ports.banco_repository_port import BancoRepositoryPort
from src.banco_preguntas.entities.ports.pregunta_repository_port import PreguntaRepositoryPort
from src.banco_preguntas.entities.pregunta_plantilla import (
    PreguntaPlantillaOpcionMultiple,
    PreguntaPlantillaVerdaderoFalso,
)


class FiltrarBancoUseCase:
    """Orquesta la consulta de preguntas activas de un banco por combinaciones de metadatos."""

    def __init__(
        self,
        banco_repositorio: BancoRepositoryPort,
        pregunta_repositorio: PreguntaRepositoryPort,
    ) -> None:
        """Recibe los repositorios de bancos y preguntas a usar."""
        self._banco_repositorio = banco_repositorio
        self._pregunta_repositorio = pregunta_repositorio

    async def execute(
        self,
        banco_id: UUID,
        unidad: str | None = None,
        tema: str | None = None,
        dificultad: str | None = None,
        importancia: str | None = None,
    ) -> list[PreguntaPlantillaOpcionMultiple | PreguntaPlantillaVerdaderoFalso]:
        """Valida que el `Banco` exista y devuelve las preguntas activas que matchean los filtros.

        Levanta `BancoNoExiste` si el banco no existe. Los filtros omitidos (`None`) no
        restringen el resultado — un banco sin preguntas cargadas devuelve lista vacía.
        """
        banco = await self._banco_repositorio.obtener_por_id(banco_id)
        if banco is None:
            raise BancoNoExiste(banco_id)

        return await self._pregunta_repositorio.filtrar(
            banco_id=banco_id,
            unidad=unidad,
            tema=tema,
            dificultad=dificultad,
            importancia=importancia,
        )
