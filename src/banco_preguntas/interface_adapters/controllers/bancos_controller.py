"""Controller de la API para operaciones de consulta sobre bancos."""

from __future__ import annotations

from uuid import UUID

from src.banco_preguntas.entities.resultado_paginado_preguntas import (
    ResultadoPaginadoPreguntas,
)
from src.banco_preguntas.use_cases.filtrar_banco import FiltrarBancoUseCase


class BancosController:
    """Adapta requests HTTP a los casos de uso de consulta sobre bancos."""

    def __init__(self, filtrar_banco: FiltrarBancoUseCase) -> None:
        """Recibe el caso de uso de filtrado del banco."""
        self._filtrar_banco = filtrar_banco

    async def filtrar_preguntas(
        self,
        banco_id: UUID,
        unidad: str | None = None,
        tema: str | None = None,
        dificultad: str | None = None,
        importancia: str | None = None,
        pagina: int | None = None,
        tamanio_pagina: int | None = None,
    ) -> ResultadoPaginadoPreguntas:
        """Delega el filtrado del banco en el caso de uso correspondiente."""
        return await self._filtrar_banco.execute(
            banco_id=banco_id,
            unidad=unidad,
            tema=tema,
            dificultad=dificultad,
            importancia=importancia,
            pagina=pagina,
            tamanio_pagina=tamanio_pagina,
        )
