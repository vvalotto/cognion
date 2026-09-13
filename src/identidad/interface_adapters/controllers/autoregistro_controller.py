"""Controller de la API para el autoregistro de cuentas sin invitación (`US-ADJ-41`/`42`)."""

from __future__ import annotations

from uuid import UUID

from src.identidad.entities.eventos import UsuarioAutoregistrado
from src.identidad.entities.usuario import Usuario
from src.identidad.use_cases.autoregistrar_docente import AutoregistrarDocenteUseCase
from src.identidad.use_cases.autoregistrar_estudiante import AutoregistrarEstudianteUseCase


class AutoregistroController:
    """Adapta requests HTTP a los casos de uso de autoregistro."""

    def __init__(
        self,
        autoregistrar_docente: AutoregistrarDocenteUseCase,
        autoregistrar_estudiante: AutoregistrarEstudianteUseCase,
    ) -> None:
        """Recibe los casos de uso de autoregistro de Docente y de Estudiante."""
        self._autoregistrar_docente = autoregistrar_docente
        self._autoregistrar_estudiante = autoregistrar_estudiante

    async def autoregistrar_docente(
        self, nombre: str, email: str, password: str
    ) -> tuple[Usuario, UsuarioAutoregistrado]:
        """Delega el autoregistro de Docente en el caso de uso correspondiente."""
        return await self._autoregistrar_docente.execute(nombre, email, password)

    async def autoregistrar_estudiante(
        self, nombre: str, email: str, password: str, comision_id: UUID
    ) -> tuple[Usuario, UsuarioAutoregistrado]:
        """Delega el autoregistro de Estudiante en el caso de uso correspondiente."""
        return await self._autoregistrar_estudiante.execute(
            nombre, email, password, comision_id
        )
