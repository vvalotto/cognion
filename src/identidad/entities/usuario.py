from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from uuid import UUID, uuid4


class TipoPerfil(str, Enum):
    ADMINISTRADOR = "administrador"
    DOCENTE = "docente"
    ESTUDIANTE = "estudiante"


@dataclass(frozen=True)
class Administrador:
    id: UUID


@dataclass(frozen=True)
class Docente:
    id: UUID


@dataclass(frozen=True)
class Estudiante:
    id: UUID


Perfil = Administrador | Docente | Estudiante


@dataclass
class Usuario:
    id: UUID
    nombre: str
    email: str
    password_hash: str
    perfil: Perfil

    @property
    def tipo_perfil(self) -> TipoPerfil:
        if isinstance(self.perfil, Administrador):
            return TipoPerfil.ADMINISTRADOR
        if isinstance(self.perfil, Docente):
            return TipoPerfil.DOCENTE
        return TipoPerfil.ESTUDIANTE

    @staticmethod
    def crear(nombre: str, email: str, password_hash: str, tipo_perfil: TipoPerfil) -> Usuario:
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
