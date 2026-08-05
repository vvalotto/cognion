"""Controller de la API para el registro de Estudiantes vía invitación."""

from __future__ import annotations

from src.identidad.entities.eventos import InvitacionAceptada, UsuarioRegistrado
from src.identidad.entities.ports.comision_repository_port import ComisionRepositoryPort
from src.identidad.entities.ports.materia_port import MateriaPort
from src.identidad.entities.usuario import Usuario
from src.identidad.use_cases.registrar_estudiante import RegistrarEstudianteUseCase


class RegistroController:
    """Adapta requests HTTP al caso de uso de registro de Estudiantes."""

    def __init__(
        self,
        registrar_estudiante: RegistrarEstudianteUseCase,
        comision_repositorio: ComisionRepositoryPort,
        materia_port: MateriaPort,
    ) -> None:
        """Recibe el caso de uso de registro y los puertos para resolver el nombre de materia."""
        self._registrar_estudiante = registrar_estudiante
        self._comision_repositorio = comision_repositorio
        self._materia_port = materia_port

    async def registrar_estudiante(
        self, token: str, nombre: str, email: str, password: str
    ) -> tuple[Usuario, str, InvitacionAceptada, UsuarioRegistrado]:
        """Delega el registro en el caso de uso y resuelve el nombre de la materia."""
        usuario, evento_invitacion, evento_usuario = await self._registrar_estudiante.execute(
            token, nombre, email, password
        )
        # La comisión y su materia existen siempre en este punto: la invitación no se genera
        # sin una comisión válida (US-1.1.1) y `CrearComisionUseCase` ya validó la materia
        # contra `MateriaPort` al crear la comisión.
        comision = await self._comision_repositorio.obtener_por_id(evento_invitacion.comision_id)
        assert comision is not None
        materia = await self._materia_port.obtener(comision.materia_id)
        assert materia is not None
        return usuario, materia.nombre, evento_invitacion, evento_usuario
