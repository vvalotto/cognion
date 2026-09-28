"""Caso de uso: filtrado del banco de preguntas de una materia por metadatos."""

from __future__ import annotations

from uuid import UUID

from src.banco_preguntas.entities.errors import BancoNoExiste, MateriaNoAutorizada
from src.banco_preguntas.entities.ports.banco_repository_port import BancoRepositoryPort
from src.banco_preguntas.entities.ports.comision_consulta_port import ComisionConsultaPort
from src.banco_preguntas.entities.ports.pregunta_repository_port import PreguntaRepositoryPort
from src.banco_preguntas.entities.resultado_paginado_preguntas import (
    ResultadoPaginadoPreguntas,
)


class FiltrarBancoUseCase:
    """Orquesta la consulta de preguntas activas de un banco por combinaciones de metadatos."""

    def __init__(
        self,
        banco_repositorio: BancoRepositoryPort,
        pregunta_repositorio: PreguntaRepositoryPort,
        comision_consulta: ComisionConsultaPort,
    ) -> None:
        """Recibe los repositorios de bancos, preguntas y el puerto de Comisión."""
        self._banco_repositorio = banco_repositorio
        self._pregunta_repositorio = pregunta_repositorio
        self._comision_consulta = comision_consulta

    async def execute(
        self,
        banco_id: UUID,
        unidad: str | None = None,
        tema: str | None = None,
        dificultad: str | None = None,
        importancia: str | None = None,
        pagina: int | None = None,
        tamanio_pagina: int | None = None,
        docente_id: UUID | None = None,
    ) -> ResultadoPaginadoPreguntas:
        """Valida que el `Banco` exista y devuelve las preguntas activas que matchean los filtros.

        Levanta `BancoNoExiste` si el banco no existe, o `MateriaNoAutorizada` (`docente_id`
        sin ninguna Comisión asignada en la materia del banco, `US-ADJ-57`). Los filtros
        omitidos (`None`) no restringen el resultado — un banco sin preguntas cargadas
        devuelve lista vacía. `pagina`/`tamanio_pagina` son opt-in (US-ADJ-03) — ver
        `PreguntaRepositoryPort.filtrar`.
        """
        banco = await self._banco_repositorio.obtener_por_id(banco_id)
        if banco is None:
            raise BancoNoExiste(banco_id)
        if docente_id is not None and not await self._comision_consulta.esta_asignado_a_materia(
            docente_id, banco.materia_id
        ):
            raise MateriaNoAutorizada(banco.materia_id)

        return await self._pregunta_repositorio.filtrar(
            banco_id=banco_id,
            unidad=unidad,
            tema=tema,
            dificultad=dificultad,
            importancia=importancia,
            pagina=pagina,
            tamanio_pagina=tamanio_pagina,
        )
