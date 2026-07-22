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
    """Perfil que rinde evaluaciones."""

    id: UUID


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
        """Crea un `Usuario` nuevo asignándole un id y el perfil correspondiente al tipo dado."""
        usuario_id = uuid4()
        perfil: Perfil
        if tipo_perfil is TipoPerfil.ADMINISTRADOR:
            perfil = Administrador(id=usuario_id)
        elif tipo_perfil is TipoPerfil.DOCENTE:
            perfil = Docente(id=usuario_id)
        else:
            perfil = Estudiante(id=usuario_id)
        return Usuario(
            id=usuario_id,
            nombre=nombre,
            email=email,
            password_hash=password_hash,
            perfil=perfil,
        )
