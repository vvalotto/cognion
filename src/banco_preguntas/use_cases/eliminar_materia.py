"""Caso de uso: baja de una materia — física si no tiene datos asociados, lógica si tiene."""

from __future__ import annotations

from uuid import UUID

from src.banco_preguntas.entities.errors import MateriaNoExiste
from src.banco_preguntas.entities.materia import Materia
from src.banco_preguntas.entities.ports.banco_repository_port import BancoRepositoryPort
from src.banco_preguntas.entities.ports.comision_consulta_port import ComisionConsultaPort
from src.banco_preguntas.entities.ports.materia_repository_port import MateriaRepositoryPort
from src.banco_preguntas.entities.ports.pregunta_repository_port import PreguntaRepositoryPort


class EliminarMateriaUseCase:
    """Da de baja una materia: física si no tiene preguntas ni comisiones, lógica si tiene."""

    def __init__(
        self,
        materia_repositorio: MateriaRepositoryPort,
        banco_repositorio: BancoRepositoryPort,
        pregunta_repositorio: PreguntaRepositoryPort,
        comision_consulta: ComisionConsultaPort,
    ) -> None:
        """Recibe los puertos de materia, banco, preguntas y consulta de comisiones a usar."""
        self._materia_repositorio = materia_repositorio
        self._banco_repositorio = banco_repositorio
        self._pregunta_repositorio = pregunta_repositorio
        self._comision_consulta = comision_consulta

    async def execute(self, materia_id: UUID) -> Materia | None:
        """Elimina o deshabilita `materia_id` según tenga preguntas o comisiones asociadas.

        Devuelve la `Materia` deshabilitada si se optó por baja lógica, o `None` si se
        eliminó físicamente. Lanza `MateriaNoExiste` si la materia (o su banco) no existe.
        """
        materia = await self._materia_repositorio.obtener_por_id(materia_id)
        if materia is None:
            raise MateriaNoExiste(materia_id)

        banco = await self._banco_repositorio.obtener_por_materia_id(materia_id)
        tiene_preguntas = banco is not None and (
            await self._pregunta_repositorio.existen_preguntas(banco.id)
        )
        tiene_comisiones = await self._comision_consulta.tiene_comisiones(materia_id)

        if tiene_preguntas or tiene_comisiones:
            materia.deshabilitar()
            await self._materia_repositorio.actualizar(materia)
            return materia

        await self._materia_repositorio.eliminar(materia_id)
        return None
