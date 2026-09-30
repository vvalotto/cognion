"""Caso de uso: autoregistro de un Estudiante sin invitación, eligiendo su Comisión."""

from __future__ import annotations

from uuid import UUID

from src.identidad.entities.errors import ComisionNoExiste, EmailYaRegistrado
from src.identidad.entities.eventos import UsuarioAutoregistrado
from src.identidad.entities.ports.comision_repository_port import ComisionRepositoryPort
from src.identidad.entities.ports.password_hasher_port import PasswordHasherPort
from src.identidad.entities.ports.usuario_repository_port import UsuarioRepositoryPort
from src.identidad.entities.usuario import Usuario


class AutoregistrarEstudianteUseCase:
    """Crea una cuenta de Estudiante activa de inmediato (INV-ID-16), sin actor autenticado."""

    def __init__(
        self,
        repositorio: UsuarioRepositoryPort,
        hasher: PasswordHasherPort,
        comision_repo: ComisionRepositoryPort,
    ) -> None:
        """Recibe el repositorio de usuarios, el hasher y el repositorio de comisiones."""
        self._repositorio = repositorio
        self._hasher = hasher
        self._comision_repo = comision_repo

    async def execute(
        self, nombre: str, email: str, password: str, comision_id: UUID
    ) -> tuple[Usuario, UsuarioAutoregistrado]:
        """Crea y persiste el Estudiante, y devuelve el usuario junto al evento emitido.

        Lanza `EmailYaRegistrado` si el email ya está en uso, `ComisionNoExiste` si
        `comision_id` no corresponde a una comisión existente (INV-ID-14), o
        `PasswordDemasiadoCorta`/`PasswordSinComplejidadSuficiente` si `password` no cumple
        INV-ID-11 (ampliada).
        """
        if await self._repositorio.existe_email(email):
            raise EmailYaRegistrado(email)

        if await self._comision_repo.obtener_por_id(comision_id) is None:
            raise ComisionNoExiste(comision_id)

        Usuario.validar_password_nueva(password)
        password_hash = self._hasher.hash(password)
        usuario = Usuario.crear_estudiante(nombre, email, password_hash, comision_id)
        await self._repositorio.guardar(usuario)

        evento = UsuarioAutoregistrado(
            usuario_id=usuario.id, email=usuario.email, tipo_perfil=usuario.tipo_perfil.value
        )
        return usuario, evento
