"""Controller de la API para el autoregistro de cuentas sin invitación (`US-ADJ-41`/`42`)."""

from __future__ import annotations

from uuid import UUID

from src.identidad.entities.ports.comision_query_port import ComisionQueryPort
from src.identidad.entities.ports.materia_port import MateriaPort
from src.identidad.interface_adapters.presenters.identidad_presenter import (
    AutoregistroSalida,
    ComisionAutoregistroSalida,
    MateriaAutoregistroSalida,
    presentar_autoregistro,
    presentar_comisiones_autoregistro,
    presentar_materias_autoregistro,
)
from src.identidad.use_cases.autoregistrar_docente import AutoregistrarDocenteUseCase
from src.identidad.use_cases.autoregistrar_estudiante import AutoregistrarEstudianteUseCase


class AutoregistroController:
    """Adapta requests HTTP a los casos de uso de autoregistro."""

    def __init__(
        self,
        autoregistrar_docente: AutoregistrarDocenteUseCase,
        autoregistrar_estudiante: AutoregistrarEstudianteUseCase,
        materia_port: MateriaPort,
        comision_query: ComisionQueryPort,
    ) -> None:
        """Recibe los casos de uso de autoregistro y los puertos de consulta del selector."""
        self._autoregistrar_docente = autoregistrar_docente
        self._autoregistrar_estudiante = autoregistrar_estudiante
        self._materia_port = materia_port
        self._comision_query = comision_query

    async def autoregistrar_docente(
        self, nombre: str, email: str, password: str
    ) -> AutoregistroSalida:
        """Delega el autoregistro de Docente en el caso de uso correspondiente."""
        usuario, _evento = await self._autoregistrar_docente.execute(nombre, email, password)
        return presentar_autoregistro(usuario)

    async def autoregistrar_estudiante(
        self, nombre: str, email: str, password: str, comision_id: UUID
    ) -> AutoregistroSalida:
        """Delega el autoregistro de Estudiante en el caso de uso correspondiente."""
        usuario, _evento = await self._autoregistrar_estudiante.execute(
            nombre, email, password, comision_id
        )
        return presentar_autoregistro(usuario)

    async def listar_materias(self) -> list[MateriaAutoregistroSalida]:
        """Lista las materias para el selector de la pantalla de autoregistro de Estudiante.

        Pass-through fino sobre `MateriaPort.listar()` — sin Use Case dedicado, mismo criterio
        que `ComisionesQueryController.obtener_comision` (`US-ADJ-25`). Endpoint público, sin
        JWT (`US-ADJ-43`).
        """
        return presentar_materias_autoregistro(await self._materia_port.listar())

    async def listar_comisiones_por_materia(
        self, materia_id: UUID
    ) -> list[ComisionAutoregistroSalida]:
        """Lista las comisiones activas de una materia para el mismo selector.

        Pass-through fino sobre `ComisionQueryPort.listar_comisiones_por_materia()`
        (`US-4.2.2`), reutilizado sin cambios. Endpoint público, sin JWT (`US-ADJ-43`).
        """
        return presentar_comisiones_autoregistro(
            await self._comision_query.listar_comisiones_por_materia(materia_id)
        )
