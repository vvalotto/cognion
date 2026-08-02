"""Schemas Pydantic de request/response de la API del BC Banco de Preguntas."""

from __future__ import annotations

from uuid import UUID

from pydantic import BaseModel, Field


class CrearMateriaRequest(BaseModel):
    """Body de la request de alta de materia."""

    nombre: str = Field(..., min_length=1, max_length=200)


class MateriaResponse(BaseModel):
    """Representación de una materia (y su banco) devuelta por la API."""

    id: UUID
    nombre: str
    banco_id: UUID
