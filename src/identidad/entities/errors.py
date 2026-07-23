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


class DocenteNoAsignadoAComision(Exception):
    """Se intentó generar una invitación con un docente que no está asignado a la comisión."""

    def __init__(self, docente_id: UUID, comision_id: UUID) -> None:
        """Guarda los ids en conflicto y arma el mensaje de la excepción."""
        self.docente_id = docente_id
        self.comision_id = comision_id
        super().__init__(
            f"El docente '{docente_id}' no está asignado a la comisión '{comision_id}'."
        )


class InvitacionNoValida(Exception):
    """Se intentó aceptar una invitación inexistente, vencida o ya usada.

    Guard genérico de `US-1.1.2` (INV-ID-01, INV-ID-03). `US-1.1.3` refina el rechazo en
    `InvitacionInvalida`, `InvitacionVencida` e `InvitacionYaUsada` según el caso — fuera
    de alcance de esta excepción.
    """

    def __init__(self, token: str) -> None:
        """Guarda el token en conflicto y arma el mensaje de la excepción."""
        self.token = token
        super().__init__(f"La invitación con token '{token}' no es válida.")
