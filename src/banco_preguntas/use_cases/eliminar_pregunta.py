"""Caso de uso: eliminación (baja lógica) de una pregunta existente del banco."""

from __future__ import annotations

from uuid import UUID

from src.banco_preguntas.entities.errors import MateriaNoAutorizada, PreguntaNoExiste
from src.banco_preguntas.entities.eventos import PreguntaEliminada
from src.banco_preguntas.entities.ports.banco_repository_port import BancoRepositoryPort
from src.banco_preguntas.entities.ports.comision_consulta_port import ComisionConsultaPort
from src.banco_preguntas.entities.ports.pregunta_repository_port import PreguntaRepositoryPort
from src.banco_preguntas.entities.pregunta_plantilla import (
    PreguntaPlantillaOpcionMultiple,
    PreguntaPlantillaVerdaderoFalso,
)


class EliminarPreguntaUseCase:
    """Orquesta la baja lógica de una pregunta."""

    def __init__(
        self,
        pregunta_repositorio: PreguntaRepositoryPort,
        banco_repositorio: BancoRepositoryPort,
        comision_consulta: ComisionConsultaPort,
    ) -> None:
        """Recibe el repositorio de preguntas, de bancos y el puerto de Comisión."""
        self._pregunta_repositorio = pregunta_repositorio
        self._banco_repositorio = banco_repositorio
        self._comision_consulta = comision_consulta

    async def execute(
        self, pregunta_id: UUID, docente_id: UUID | None = None
    ) -> tuple[
        PreguntaPlantillaOpcionMultiple | PreguntaPlantillaVerdaderoFalso, PreguntaEliminada
    ]:
        """Marca la pregunta como inactiva y persiste el cambio.

        Levanta `PreguntaNoExiste` si la pregunta no existe, `PreguntaYaEliminada` (propagada
        desde la entidad) si ya estaba inactiva, o `MateriaNoAutorizada` (`docente_id` sin
        ninguna Comisión asignada en la materia del banco de la pregunta, `US-ADJ-57`).
        """
        pregunta = await self._pregunta_repositorio.obtener_por_id(pregunta_id)
        if pregunta is None:
            raise PreguntaNoExiste(pregunta_id)

        if docente_id is not None:
            banco = await self._banco_repositorio.obtener_por_id(pregunta.banco_id)
            assert banco is not None, f"Pregunta {pregunta_id} con banco_id inexistente"
            if not await self._comision_consulta.esta_asignado_a_materia(
                docente_id, banco.materia_id
            ):
                raise MateriaNoAutorizada(banco.materia_id)

        pregunta.eliminar()

        await self._pregunta_repositorio.actualizar(pregunta)

        evento = PreguntaEliminada(pregunta_id=pregunta.id, banco_id=pregunta.banco_id)
        return pregunta, evento
