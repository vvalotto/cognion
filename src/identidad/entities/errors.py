"""Errores de dominio del BC Identidad."""

from __future__ import annotations

from uuid import UUID

from src.identidad.entities.eventos import CuentaBloqueada


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


class InvitacionInvalida(Exception):
    """Se intentó aceptar una invitación cuyo token no corresponde a ninguna existente."""

    def __init__(self, token: str) -> None:
        """Guarda el token en conflicto y arma el mensaje de la excepción."""
        self.token = token
        super().__init__(f"La invitación con token '{token}' no existe.")


class InvitacionVencida(Exception):
    """Se intentó aceptar una invitación cuyo `expira_en` ya pasó (INV-ID-03)."""

    def __init__(self, token: str) -> None:
        """Guarda el token en conflicto y arma el mensaje de la excepción."""
        self.token = token
        super().__init__(f"La invitación con token '{token}' ya venció.")


class InvitacionYaUsada(Exception):
    """Se intentó aceptar una invitación con `usada_en` no null (INV-ID-01)."""

    def __init__(self, token: str) -> None:
        """Guarda el token en conflicto y arma el mensaje de la excepción."""
        self.token = token
        super().__init__(f"La invitación con token '{token}' ya fue utilizada.")


class MateriaNoExiste(Exception):
    """Se referenció una materia que no existe en BC Banco de Preguntas."""

    def __init__(self, materia_id: UUID) -> None:
        """Guarda el id de la materia en conflicto y arma el mensaje de la excepción."""
        self.materia_id = materia_id
        super().__init__(f"La materia '{materia_id}' no existe.")


class CredencialesInvalidas(Exception):
    """El email no existe o la contraseña no verifica contra el hash guardado.

    El mensaje no distingue entre ambos casos para no filtrar si una cuenta existe
    (`US-1.1.4`). Cuando el fallo es el 3er intento consecutivo, `evento_cuenta_bloqueada`
    lleva el evento `CuentaBloqueada` emitido junto con el rechazo (`US-2.2.1`).
    """

    def __init__(self) -> None:
        """Arma el mensaje genérico de la excepción, sin datos del intento fallido."""
        self.evento_cuenta_bloqueada: CuentaBloqueada | None = None
        super().__init__("Email o contraseña inválidos.")


class CuentaBloqueadaError(Exception):
    """La cuenta llegó a 3 intentos fallidos consecutivos y está bloqueada (INV-ID-10).

    Solo se desbloquea mediante reseteo de contraseña por un Administrador (`US-2.2.4`).
    """

    def __init__(self, usuario_id: UUID) -> None:
        """Guarda el id de la cuenta bloqueada y arma el mensaje de la excepción."""
        self.usuario_id = usuario_id
        super().__init__("La cuenta está bloqueada. Contactá a un administrador.")


class UsuarioNoExiste(Exception):
    """Se referenció un usuario que no está registrado (`US-2.2.3`)."""

    def __init__(self, usuario_id: UUID) -> None:
        """Guarda el id del usuario en conflicto y arma el mensaje de la excepción."""
        self.usuario_id = usuario_id
        super().__init__(f"El usuario '{usuario_id}' no existe.")


class PasswordDemasiadoCorta(Exception):
    """La contraseña nueva no cumple el mínimo de 8 caracteres (INV-ID-11)."""

    def __init__(self) -> None:
        """Arma el mensaje genérico de la excepción, sin datos de la contraseña rechazada."""
        super().__init__("La contraseña debe tener al menos 8 caracteres.")


class PasswordActualIncorrecta(Exception):
    """La contraseña actual provista no verifica contra el hash guardado (`US-2.2.5`).

    Cuando el fallo es el 3er intento consecutivo de este flujo, `evento_cuenta_bloqueada`
    lleva el evento `CuentaBloqueada` emitido junto con el rechazo (INV-ID-10).
    """

    def __init__(self) -> None:
        """Arma el mensaje genérico de la excepción, sin datos del intento fallido."""
        self.evento_cuenta_bloqueada: CuentaBloqueada | None = None
        super().__init__("La contraseña actual es incorrecta.")
