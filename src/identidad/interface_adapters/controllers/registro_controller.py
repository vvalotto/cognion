"""Controller de la API para el registro de Estudiantes vía invitación."""

from __future__ import annotations

from src.identidad.entities.eventos import InvitacionAceptada, UsuarioRegistrado
from src.identidad.entities.usuario import Usuario
from src.identidad.use_cases.registrar_estudiante import RegistrarEstudianteUseCase


class RegistroController:
    """Adapta requests HTTP al caso de uso de registro de Estudiantes."""

    def __init__(self, registrar_estudiante: RegistrarEstudianteUseCase) -> None:
        """Recibe el caso de uso de registro de estudiante a usar."""
        self._registrar_estudiante = registrar_estudiante

    async def registrar_estudiante(
        self, token: str, nombre: str, email: str, password: str
    ) -> tuple[Usuario, InvitacionAceptada, UsuarioRegistrado]:
        """Delega el registro del estudiante en el caso de uso correspondiente."""
        return await self._registrar_estudiante.execute(token, nombre, email, password)
