"""Adaptador de `PreguntaConsultaPort` — llamada in-process a BC Banco de Preguntas.

Mismo criterio de acoplamiento consciente que `materia_consulta_port_in_process.py`. Cuenta las
preguntas activas resolviendo primero el `Banco` de la materia (1:1, INV-BP-01) y reutilizando
`PreguntaRepositoryPort.filtrar()` para el conteo — mismo criterio que `ListarMateriasUseCase`
(`US-2.1.9`), sin ensanchar ese puerto.
"""

from __future__ import annotations

from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from src.actividad_evaluativa.entities.ports.pregunta_consulta_port import PreguntaConsultaPort
from src.banco_preguntas.interface_adapters.gateways.banco_repository import (
    SQLAlchemyBancoRepository,
)
from src.banco_preguntas.interface_adapters.gateways.pregunta_repository import (
    SQLAlchemyPreguntaRepository,
)


class PreguntaConsultaPortInProcess(PreguntaConsultaPort):
    """Implementa `PreguntaConsultaPort` invocando repositorios de Banco de Preguntas in-process."""

    def __init__(self, session: AsyncSession) -> None:
        """Recibe la sesión async compartida con los repositorios de Banco y Pregunta."""
        self._banco_repositorio = SQLAlchemyBancoRepository(session)
        self._pregunta_repositorio = SQLAlchemyPreguntaRepository(session)

    async def contar_activas_por_materia(self, materia_id: UUID) -> int:
        """Cuenta las preguntas `activa = true` del banco de la materia.

        Devuelve 0 si la materia no tiene `Banco` asociado — no debería ocurrir en la práctica
        (INV-BP-01, toda `Materia` se crea junto con su `Banco`), pero evita que este puerto le
        exija a su llamador conocer ese invariante interno de Banco de Preguntas.
        """
        banco = await self._banco_repositorio.obtener_por_materia_id(materia_id)
        if banco is None:
            return 0
        resultado = await self._pregunta_repositorio.filtrar(banco.id)
        return resultado.total

    async def listar_ids_activas_por_materia(self, materia_id: UUID) -> list[UUID]:
        """Lista los ids de las preguntas `activa = true` del banco de la materia.

        Lista vacía si la materia no tiene `Banco` asociado — mismo criterio que
        `contar_activas_por_materia`.
        """
        banco = await self._banco_repositorio.obtener_por_materia_id(materia_id)
        if banco is None:
            return []
        resultado = await self._pregunta_repositorio.filtrar(banco.id)
        return [pregunta.id for pregunta in resultado.preguntas]
