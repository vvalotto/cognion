"""Caso de uso: carga de una pregunta de opción múltiple en el banco de una materia."""

from __future__ import annotations

from uuid import UUID

from src.banco_preguntas.entities.dificultad import Dificultad
from src.banco_preguntas.entities.errors import BancoNoExiste
from src.banco_preguntas.entities.eventos import PreguntaCargada
from src.banco_preguntas.entities.importancia import Importancia
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
        texto: str,
        opciones: list[Opcion],
        unidad_tematica: str,
        tema: str,
        dificultad: Dificultad,
        importancia: Importancia,
    ) -> tuple[PreguntaPlantillaOpcionMultiple, PreguntaCargada]:
        """Valida que el `Banco` exista, crea y persiste la pregunta.

        Levanta `BancoNoExiste` u `OpcionesInvalidas`.
        """
        banco = await self._banco_repositorio.obtener_por_id(banco_id)
        if banco is None:
            raise BancoNoExiste(banco_id)

        pregunta = PreguntaPlantillaOpcionMultiple.crear(
            banco_id=banco_id,
            texto=texto,
            opciones=opciones,
            unidad_tematica=unidad_tematica,
            tema=tema,
            dificultad=dificultad,
            importancia=importancia,
        )
        await self._pregunta_repositorio.guardar(pregunta)

        evento = PreguntaCargada(pregunta_id=pregunta.id, banco_id=banco_id)
        return pregunta, evento
