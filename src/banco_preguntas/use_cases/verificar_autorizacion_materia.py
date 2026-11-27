"""Servicio compartido de autorización por materia (`US-ADJ-57`)."""

from __future__ import annotations

from uuid import UUID

from src.banco_preguntas.entities.errors import BancoNoExiste, MateriaNoAutorizada
from src.banco_preguntas.entities.ports.banco_repository_port import BancoRepositoryPort
from src.banco_preguntas.entities.ports.comision_consulta_port import ComisionConsultaPort


class VerificarAutorizacionMateriaService:
    """Encapsula `BancoRepositoryPort` + `ComisionConsultaPort` tras un único dependiente.

    La autorización del Docente por materia es una responsabilidad propia, compartida por varios
    casos de uso de preguntas (`US-ADJ-57`): se resuelve en un solo lugar.
    """

    def __init__(
        self, banco_repositorio: BancoRepositoryPort, comision_consulta: ComisionConsultaPort
    ) -> None:
        """Recibe el repositorio de bancos y el puerto de consulta de Comisión."""
        self._banco_repositorio = banco_repositorio
        self._comision_consulta = comision_consulta

    async def verificar(self, banco_id: UUID, docente_id: UUID | None) -> None:
        """No-op si `docente_id` es `None` (Administrador, sin filtro).

        Levanta `BancoNoExiste` si el banco no existe, `MateriaNoAutorizada` si el Docente no
        tiene ninguna Comisión asignada en su materia.
        """
        if docente_id is None:
            return
        banco = await self._banco_repositorio.obtener_por_id(banco_id)
        if banco is None:
            raise BancoNoExiste(banco_id)
        if not await self._comision_consulta.esta_asignado_a_materia(docente_id, banco.materia_id):
            raise MateriaNoAutorizada(banco.materia_id)
