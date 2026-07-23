"""Schemas Pydantic de request/response de la API del BC Identidad."""

from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field

from src.identidad.entities.usuario import TipoPerfil


class CrearUsuarioRequest(BaseModel):
    """Body de la request de alta de usuario."""

    nombre: str = Field(..., min_length=1, max_length=200)
    email: str = Field(..., min_length=3, max_length=255)
    password: str = Field(..., min_length=8)
    perfil: TipoPerfil


class UsuarioResponse(BaseModel):
    """Representación de un usuario devuelta por la API."""

    id: UUID
    nombre: str
    email: str
    perfil: TipoPerfil


class CrearComisionRequest(BaseModel):
    """Body de la request de alta de comisión."""

    materia: str = Field(..., min_length=1, max_length=200)
    horario: str = Field(..., min_length=1, max_length=200)
    administrador_id: UUID


class ComisionResponse(BaseModel):
    """Representación de una comisión devuelta por la API."""

    id: UUID
    materia: str
    horario: str
    administrador_id: UUID
    docentes_asignados: list[UUID]


class AsignarDocenteRequest(BaseModel):
    """Body de la request de asignación de un docente a una comisión."""

    docente_id: UUID


class GenerarInvitacionRequest(BaseModel):
    """Body de la request de generación de una invitación."""

    docente_id: UUID
    email_destinatario: str = Field(..., min_length=3, max_length=255)


class InvitacionResponse(BaseModel):
    """Representación de una invitación devuelta por la API."""

    id: UUID
    comision_id: UUID
    docente_id: UUID
    expira_en: datetime


class RegistrarEstudianteRequest(BaseModel):
    """Body de la request de registro de un Estudiante vía invitación."""

    token: str = Field(..., min_length=1)
    nombre: str = Field(..., min_length=1, max_length=200)
    email: str = Field(..., min_length=3, max_length=255)
    password: str = Field(..., min_length=8)


class RegistroResponse(BaseModel):
    """Representación del Estudiante registrado devuelta por la API."""

    id: UUID
    nombre: str
    email: str
    comision_id: UUID


class LoginRequest(BaseModel):
    """Body de la request de autenticación."""

    email: str = Field(..., min_length=3, max_length=255)
    password: str = Field(..., min_length=1)


class LoginResponse(BaseModel):
    """JWT emitido tras una autenticación exitosa (RF-02)."""

    access_token: str
    token_type: str = "bearer"
    rol: TipoPerfil
    expira_en: datetime
