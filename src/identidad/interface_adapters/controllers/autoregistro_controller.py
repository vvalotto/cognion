"""Controller de la API para el autoregistro de cuentas sin invitación (`US-ADJ-41`)."""

from __future__ import annotations

from src.identidad.entities.eventos import UsuarioAutoregistrado
from src.identidad.entities.usuario import Usuario
from src.identidad.use_cases.autoregistrar_docente import AutoregistrarDocenteUseCase


class AutoregistroController:
    """Adapta requests HTTP a los casos de uso de autoregistro."""

    def __init__(self, autoregistrar_docente: AutoregistrarDocenteUseCase) -> None:
        """Recibe el caso de uso de autoregistro de Docente."""
        self._autoregistrar_docente = autoregistrar_docente

    async def autoregistrar_docente(
        self, nombre: str, email: str, password: str
    ) -> tuple[Usuario, UsuarioAutoregistrado]:
        """Delega el autoregistro de Docente en el caso de uso correspondiente."""
        return await self._autoregistrar_docente.execute(nombre, email, password)
