"""Usuario y sus perfiles posibles dentro del BC Identidad."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime
from uuid import UUID, uuid4

from src.identidad.entities.errors import PasswordDemasiadoCorta
from src.shared.entities.tipo_perfil import TipoPerfil

_LARGO_MINIMO_PASSWORD = 8
_INTENTOS_MAXIMOS_CAMBIO_PASSWORD = 3


def _ahora() -> datetime:
    """Devuelve el instante actual en UTC."""
    return datetime.now(UTC)


@dataclass(frozen=True)
class Administrador:
    """Perfil con permisos de administración de comisiones."""

    id: UUID


@dataclass(frozen=True)
class Docente:
    """Perfil asignable a comisiones para evaluar."""

    id: UUID


@dataclass(frozen=True)
class Estudiante:
    """Perfil que rinde evaluaciones, asignado a una comisión desde su creación (INV-ID-05)."""

    id: UUID
    comision_id: UUID


Perfil = Administrador | Docente | Estudiante


@dataclass
class Usuario:
    """Cuenta de una persona registrada en la plataforma."""

    id: UUID
    nombre: str
    email: str
    password_hash: str
    perfil: Perfil
    bloqueada: bool = False
    intentos_fallidos_login: int = 0
    intentos_fallidos_password: int = 0
    creado_en: datetime = field(default_factory=_ahora)

    @property
    def tipo_perfil(self) -> TipoPerfil:
        """Devuelve el `TipoPerfil` correspondiente al perfil concreto del usuario."""
        if isinstance(self.perfil, Administrador):
            return TipoPerfil.ADMINISTRADOR
        if isinstance(self.perfil, Docente):
            return TipoPerfil.DOCENTE
        return TipoPerfil.ESTUDIANTE

    @staticmethod
    def crear(nombre: str, email: str, password_hash: str, tipo_perfil: TipoPerfil) -> Usuario:
        """Crea un `Usuario` nuevo con perfil `Administrador` o `Docente`.

        `Estudiante` no se crea por esta vía porque requiere `comision_id` — usar
        `Usuario.crear_estudiante` (INV-ID-05, único camino: registro vía invitación).
        """
        if tipo_perfil is TipoPerfil.ESTUDIANTE:
            raise ValueError(
                "Estudiante no se crea con Usuario.crear() — usar Usuario.crear_estudiante()."
            )
        usuario_id = uuid4()
        perfil: Perfil = (
            Administrador(id=usuario_id)
            if tipo_perfil is TipoPerfil.ADMINISTRADOR
            else Docente(id=usuario_id)
        )
        return Usuario(
            id=usuario_id,
            nombre=nombre,
            email=email,
            password_hash=password_hash,
            perfil=perfil,
        )

    @staticmethod
    def validar_password_nueva(password_nueva: str) -> None:
        """Valida INV-ID-11 sobre una contraseña en texto plano, antes de hashearla.

        Lanza `PasswordDemasiadoCorta` si no llega al mínimo de 8 caracteres.
        """
        if len(password_nueva) < _LARGO_MINIMO_PASSWORD:
            raise PasswordDemasiadoCorta()

    def resetear_password(self, password_hash_nuevo: str) -> bool:
        """Fija `password_hash_nuevo` y desbloquea la cuenta si estaba bloqueada.

        Resetea `intentos_fallidos_login` e `intentos_fallidos_password` a 0 en ambos casos.
        Devuelve `True` si la cuenta estaba bloqueada antes del reseteo (el llamador decide si
        corresponde emitir `CuentaDesbloqueada`).
        """
        estaba_bloqueada = self.bloqueada
        self.password_hash = password_hash_nuevo
        self.bloqueada = False
        self.intentos_fallidos_login = 0
        self.intentos_fallidos_password = 0
        return estaba_bloqueada

    def cambiar_password(self, password_hash_nuevo: str) -> None:
        """Fija `password_hash_nuevo` y resetea `intentos_fallidos_password` a 0.

        Se usa tras verificar la contraseña actual y validar la nueva (`US-2.2.5`) — no toca
        `bloqueada` ni `intentos_fallidos_login`, contadores independientes de este flujo.
        """
        self.password_hash = password_hash_nuevo
        self.intentos_fallidos_password = 0

    def registrar_fallo_cambio_password(self) -> bool:
        """Registra un intento fallido de cambio de la propia contraseña (INV-ID-10).

        Incrementa `intentos_fallidos_password`; al 3er fallo consecutivo bloquea la cuenta.
        Devuelve `True` si este fallo bloqueó la cuenta (el llamador decide si corresponde
        emitir `CuentaBloqueada`).
        """
        self.intentos_fallidos_password += 1
        if self.intentos_fallidos_password >= _INTENTOS_MAXIMOS_CAMBIO_PASSWORD:
            self.bloqueada = True
            return True
        return False

    @staticmethod
    def crear_estudiante(nombre: str, email: str, password_hash: str, comision_id: UUID) -> Usuario:
        """Crea un `Usuario` nuevo con perfil `Estudiante` asignado a `comision_id` (INV-ID-05)."""
        usuario_id = uuid4()
        return Usuario(
            id=usuario_id,
            nombre=nombre,
            email=email,
            password_hash=password_hash,
            perfil=Estudiante(id=usuario_id, comision_id=comision_id),
        )
