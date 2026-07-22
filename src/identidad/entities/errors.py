"""Errores de dominio del BC Identidad."""

from __future__ import annotations

from uuid import UUID


class EmailYaRegistrado(Exception):
    """Se intentó registrar un usuario con un email ya existente."""

    def __init__(self, email: str) -> None:
        """Guarda el email en conflicto y arma el mensaje de la excepción."""
        self.email = email
        super().__init__(f"El email '{email}' ya está registrado.")


class UsuarioNoEsDocente(Exception):
    """Se intentó asignar como docente a un usuario que no tiene ese perfil."""

    def __init__(self, usuario_id: UUID) -> None:
        """Guarda el id del usuario en conflicto y arma el mensaje de la excepción."""
        self.usuario_id = usuario_id
        super().__init__(f"El usuario '{usuario_id}' no tiene perfil Docente.")


class ComisionNoExiste(Exception):
    """Se referenció una comisión que no está registrada."""

    def __init__(self, comision_id: UUID) -> None:
        """Guarda el id de la comisión en conflicto y arma el mensaje de la excepción."""
        self.comision_id = comision_id
        super().__init__(f"La comisión '{comision_id}' no existe.")
