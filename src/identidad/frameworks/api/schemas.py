from __future__ import annotations

from uuid import UUID

from pydantic import BaseModel, Field

from src.identidad.entities.usuario import TipoPerfil


class CrearUsuarioRequest(BaseModel):
    nombre: str = Field(..., min_length=1, max_length=200)
    email: str = Field(..., min_length=3, max_length=255)
    password: str = Field(..., min_length=8)
    perfil: TipoPerfil


class UsuarioResponse(BaseModel):
    id: UUID
    nombre: str
    email: str
    perfil: TipoPerfil


class CrearComisionRequest(BaseModel):
    materia: str = Field(..., min_length=1, max_length=200)
    horario: str = Field(..., min_length=1, max_length=200)
    administrador_id: UUID


class ComisionResponse(BaseModel):
    id: UUID
    materia: str
    horario: str
    administrador_id: UUID
    docentes_asignados: list[UUID]


class AsignarDocenteRequest(BaseModel):
    docente_id: UUID
