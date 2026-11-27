"""Presenters de Banco de Preguntas (`ADR-031`): entidades -> tipos de salida de la API.

Los `dataclass` de salida tienen los mismos campos que los esquemas de `frameworks/api/schemas.py`;
FastAPI los valida contra el `response_model` sin código extra. Sin Pydantic ni FastAPI.
"""

from __future__ import annotations

from dataclasses import dataclass
from uuid import UUID

from src.banco_preguntas.entities.banco import Banco
from src.banco_preguntas.entities.dificultad import Dificultad
from src.banco_preguntas.entities.importancia import Importancia
from src.banco_preguntas.entities.materia import Materia
from src.banco_preguntas.entities.pregunta_plantilla import (
    PreguntaPlantillaOpcionMultiple,
    PreguntaPlantillaVerdaderoFalso,
)
from src.banco_preguntas.entities.resultado_paginado_preguntas import ResultadoPaginadoPreguntas


@dataclass(frozen=True)
class MateriaSalida:
    """Una materia recién creada junto con el id de su banco."""

    id: UUID
    nombre: str
    banco_id: UUID


@dataclass(frozen=True)
class MateriaBasicaSalida:
    """Una materia sin su banco (alcanza para edición y baja)."""

    id: UUID
    nombre: str
    activa: bool


@dataclass(frozen=True)
class MateriaListItemSalida:
    """Una materia del listado, con la cantidad de preguntas activas de su banco."""

    id: UUID
    nombre: str
    banco_id: UUID
    cantidad_preguntas_activas: int
    activa: bool


@dataclass(frozen=True)
class OpcionSalida:
    """Una opción de respuesta de una pregunta de opción múltiple."""

    texto: str
    es_correcta: bool


@dataclass(frozen=True)
class PreguntaOpcionMultipleSalida:
    """Una pregunta de opción múltiple."""

    id: UUID
    banco_id: UUID
    texto: str
    opciones: list[OpcionSalida]
    unidad_tematica: str
    tema: str
    dificultad: Dificultad
    importancia: Importancia
    activa: bool


@dataclass(frozen=True)
class PreguntaVerdaderoFalsoSalida:
    """Una pregunta Verdadero/Falso."""

    id: UUID
    banco_id: UUID
    texto: str
    respuesta_correcta: bool
    unidad_tematica: str
    tema: str
    dificultad: Dificultad
    importancia: Importancia
    activa: bool


PreguntaSalida = PreguntaOpcionMultipleSalida | PreguntaVerdaderoFalsoSalida


@dataclass(frozen=True)
class PreguntasPaginadasSalida:
    """Una página de preguntas junto con el total que cumple los filtros."""

    preguntas: list[PreguntaSalida]
    total: int


def presentar_materia_creada(materia: Materia, banco: Banco) -> MateriaSalida:
    """Arma la salida de una materia recién creada."""
    return MateriaSalida(id=materia.id, nombre=materia.nombre, banco_id=banco.id)


def presentar_materia_basica(materia: Materia) -> MateriaBasicaSalida:
    """Arma la salida de una materia sin banco."""
    return MateriaBasicaSalida(id=materia.id, nombre=materia.nombre, activa=materia.activa)


def presentar_materias(items: list[tuple[Materia, Banco, int]]) -> list[MateriaListItemSalida]:
    """Arma el listado de materias con su banco y la cantidad de preguntas activas."""
    return [
        MateriaListItemSalida(
            id=materia.id,
            nombre=materia.nombre,
            banco_id=banco.id,
            cantidad_preguntas_activas=cantidad,
            activa=materia.activa,
        )
        for materia, banco, cantidad in items
    ]


def presentar_pregunta_opcion_multiple(
    pregunta: PreguntaPlantillaOpcionMultiple,
) -> PreguntaOpcionMultipleSalida:
    """Arma la salida de una pregunta de opción múltiple."""
    return PreguntaOpcionMultipleSalida(
        id=pregunta.id,
        banco_id=pregunta.banco_id,
        texto=pregunta.texto,
        opciones=[
            OpcionSalida(texto=o.texto, es_correcta=o.es_correcta) for o in pregunta.opciones
        ],
        unidad_tematica=pregunta.unidad_tematica,
        tema=pregunta.tema,
        dificultad=pregunta.dificultad,
        importancia=pregunta.importancia,
        activa=pregunta.activa,
    )


def presentar_pregunta_verdadero_falso(
    pregunta: PreguntaPlantillaVerdaderoFalso,
) -> PreguntaVerdaderoFalsoSalida:
    """Arma la salida de una pregunta Verdadero/Falso."""
    return PreguntaVerdaderoFalsoSalida(
        id=pregunta.id,
        banco_id=pregunta.banco_id,
        texto=pregunta.texto,
        respuesta_correcta=pregunta.respuesta_correcta,
        unidad_tematica=pregunta.unidad_tematica,
        tema=pregunta.tema,
        dificultad=pregunta.dificultad,
        importancia=pregunta.importancia,
        activa=pregunta.activa,
    )


def presentar_pregunta(
    pregunta: PreguntaPlantillaOpcionMultiple | PreguntaPlantillaVerdaderoFalso,
) -> PreguntaSalida:
    """Arma la salida de una pregunta según su tipo."""
    if isinstance(pregunta, PreguntaPlantillaOpcionMultiple):
        return presentar_pregunta_opcion_multiple(pregunta)
    return presentar_pregunta_verdadero_falso(pregunta)


def presentar_preguntas_paginadas(
    resultado: ResultadoPaginadoPreguntas,
) -> PreguntasPaginadasSalida:
    """Arma la página de preguntas del filtrado de un banco."""
    return PreguntasPaginadasSalida(
        preguntas=[presentar_pregunta(p) for p in resultado.preguntas], total=resultado.total
    )
