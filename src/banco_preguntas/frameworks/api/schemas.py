"""Schemas Pydantic de request/response de la API del BC Banco de Preguntas."""

from __future__ import annotations

from uuid import UUID

from pydantic import BaseModel, Field

from src.banco_preguntas.entities.dificultad import Dificultad
from src.banco_preguntas.entities.importancia import Importancia


class CrearMateriaRequest(BaseModel):
    """Body de la request de alta de materia."""

    nombre: str = Field(..., min_length=1, max_length=200)


class MateriaResponse(BaseModel):
    """Representación de una materia (y su banco) devuelta por la API."""

    id: UUID
    nombre: str
    banco_id: UUID


class OpcionSchema(BaseModel):
    """Una opción de respuesta en el body de la request."""

    texto: str = Field(..., min_length=1, max_length=500)
    es_correcta: bool


class CargarPreguntaOpcionMultipleRequest(BaseModel):
    """Body de la request de carga de pregunta de opción múltiple."""

    banco_id: UUID
    texto: str = Field(..., min_length=1, max_length=2000)
    opciones: list[OpcionSchema]
    unidad_tematica: str = Field(..., min_length=1, max_length=200)
    tema: str = Field(..., min_length=1, max_length=200)
    dificultad: Dificultad
    importancia: Importancia


class PreguntaOpcionMultipleResponse(BaseModel):
    """Representación de una pregunta de opción múltiple devuelta por la API."""

    id: UUID
    banco_id: UUID
    texto: str
    opciones: list[OpcionSchema]
    unidad_tematica: str
    tema: str
    dificultad: Dificultad
    importancia: Importancia
    activa: bool


class CargarPreguntaVerdaderoFalsoRequest(BaseModel):
    """Body de la request de carga de pregunta Verdadero/Falso."""

    banco_id: UUID
    texto: str = Field(..., min_length=1, max_length=2000)
    respuesta_correcta: bool
    unidad_tematica: str = Field(..., min_length=1, max_length=200)
    tema: str = Field(..., min_length=1, max_length=200)
    dificultad: Dificultad
    importancia: Importancia


class EditarPreguntaRequest(BaseModel):
    """Body de la request de edición de pregunta.

    `opciones` aplica solo si la pregunta es de opción múltiple; `respuesta_correcta` solo si
    es Verdadero/Falso — el tipo no es editable, se infiere de la pregunta ya persistida.
    """

    texto: str = Field(..., min_length=1, max_length=2000)
    unidad_tematica: str = Field(..., min_length=1, max_length=200)
    tema: str = Field(..., min_length=1, max_length=200)
    dificultad: Dificultad
    importancia: Importancia
    opciones: list[OpcionSchema] | None = None
    respuesta_correcta: bool | None = None


class PreguntaVerdaderoFalsoResponse(BaseModel):
    """Representación de una pregunta Verdadero/Falso devuelta por la API."""

    id: UUID
    banco_id: UUID
    texto: str
    respuesta_correcta: bool
    unidad_tematica: str
    tema: str
    dificultad: Dificultad
    importancia: Importancia
    activa: bool
