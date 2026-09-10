"""Caso de uso: corrección de nombre/email de una cuenta existente."""

from __future__ import annotations

from uuid import UUID

from src.identidad.entities.errors import EmailYaRegistrado, UsuarioNoExiste
from src.identidad.entities.ports.usuario_repository_port import UsuarioRepositoryPort
from src.identidad.entities.usuario import Usuario


class EditarCuentaUseCase:
    """Corrige nombre/email de una cuenta ya existente (RF-03) — sin tocar password ni perfil."""

    def __init__(self, usuario_repositorio: UsuarioRepositoryPort) -> None:
        """Recibe el repositorio de usuarios a usar."""
        self._usuario_repositorio = usuario_repositorio

    async def execute(self, usuario_id: UUID, nombre: str, email: str) -> Usuario:
        """Edita `usuario_id` con `nombre`/`email` nuevos y devuelve la cuenta actualizada.

        Lanza `UsuarioNoExiste` si la cuenta no existe, `EmailYaRegistrado` si el email nuevo
        ya pertenece a otra cuenta (no valida contra sí mismo, si el email no cambió).
        """
        usuario = await self._usuario_repositorio.obtener_por_id(usuario_id)
        if usuario is None:
            raise UsuarioNoExiste(usuario_id)

        if email != usuario.email:
            existente = await self._usuario_repositorio.obtener_por_email(email)
            if existente is not None:
                raise EmailYaRegistrado(email)

        usuario.editar_datos(nombre, email)
        await self._usuario_repositorio.actualizar(usuario)
        return usuario
