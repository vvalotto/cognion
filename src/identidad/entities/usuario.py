"""Usuario y sus perfiles posibles dentro del BC Identidad."""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
from uuid import UUID, uuid4


class TipoPerfil(StrEnum):
    """Rol de un usuario dentro de la plataforma."""

    ADMINISTRADOR = "administrador"
    DOCENTE = "docente"
    ESTUDIANTE = "estudiante"


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
