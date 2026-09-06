"""Caso de uso: carga de una pregunta de opción múltiple en el banco de una materia."""

from __future__ import annotations

from uuid import UUID

from src.banco_preguntas.entities.errors import BancoNoExiste
from src.banco_preguntas.entities.eventos import PreguntaCargada
from src.banco_preguntas.entities.metadatos_pregunta import MetadatosPregunta
from src.banco_preguntas.entities.opcion import Opcion
from src.banco_preguntas.entities.ports.banco_repository_port import BancoRepositoryPort
from src.banco_preguntas.entities.ports.pregunta_repository_port import PreguntaRepositoryPort
from src.banco_preguntas.entities.pregunta_plantilla import PreguntaPlantillaOpcionMultiple


class CargarPreguntaOpcionMultipleUseCase:
    """Orquesta la carga de una pregunta de opción múltiple (INV-BP-02, INV-BP-03)."""

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
        metadatos: MetadatosPregunta,
        opciones: list[Opcion],
    ) -> tuple[PreguntaPlantillaOpcionMultiple, PreguntaCargada]:
        """Valida que el `Banco` exista, crea y persiste la pregunta.

        Levanta `BancoNoExiste` u `OpcionesInvalidas`.
        """
        banco = await self._banco_repositorio.obtener_por_id(banco_id)
        if banco is None:
            raise BancoNoExiste(banco_id)

        pregunta = PreguntaPlantillaOpcionMultiple.crear(
            banco_id=banco_id,
            metadatos=metadatos,
            opciones=opciones,
        )
        await self._pregunta_repositorio.guardar(pregunta)

        evento = PreguntaCargada(pregunta_id=pregunta.id, banco_id=banco_id)
        return pregunta, evento
