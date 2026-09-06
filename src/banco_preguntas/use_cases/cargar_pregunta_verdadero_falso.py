"""Caso de uso: carga de una pregunta Verdadero/Falso en el banco de una materia."""

from __future__ import annotations

from uuid import UUID

from src.banco_preguntas.entities.errors import BancoNoExiste
from src.banco_preguntas.entities.eventos import PreguntaCargada
from src.banco_preguntas.entities.metadatos_pregunta import MetadatosPregunta
from src.banco_preguntas.entities.ports.banco_repository_port import BancoRepositoryPort
from src.banco_preguntas.entities.ports.pregunta_repository_port import PreguntaRepositoryPort
from src.banco_preguntas.entities.pregunta_plantilla import PreguntaPlantillaVerdaderoFalso


class CargarPreguntaVerdaderoFalsoUseCase:
    """Orquesta la carga de una pregunta de Verdadero/Falso."""

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
        respuesta_correcta: bool,
    ) -> tuple[PreguntaPlantillaVerdaderoFalso, PreguntaCargada]:
        """Valida que el `Banco` exista, crea y persiste la pregunta.

        Levanta `BancoNoExiste`.
        """
        banco = await self._banco_repositorio.obtener_por_id(banco_id)
        if banco is None:
            raise BancoNoExiste(banco_id)

        pregunta = PreguntaPlantillaVerdaderoFalso.crear(
            banco_id=banco_id,
            metadatos=metadatos,
            respuesta_correcta=respuesta_correcta,
        )
        await self._pregunta_repositorio.guardar(pregunta)

        evento = PreguntaCargada(pregunta_id=pregunta.id, banco_id=banco_id)
        return pregunta, evento
