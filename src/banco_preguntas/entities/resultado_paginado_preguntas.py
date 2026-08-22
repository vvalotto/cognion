"""Resultado de una consulta de preguntas, paginada o no (US-ADJ-03)."""

from __future__ import annotations

from dataclasses import dataclass

from src.banco_preguntas.entities.pregunta_plantilla import (
    PreguntaPlantillaOpcionMultiple,
    PreguntaPlantillaVerdaderoFalso,
)


@dataclass(frozen=True)
class ResultadoPaginadoPreguntas:
    """Página de preguntas junto con el total que matchea los filtros, sin paginar.

    Cuando la consulta no pide paginación (`pagina`/`tamanio_pagina` en `None`),
    `preguntas` trae todas las que matchean los filtros y `total` es su misma cantidad.
    """

    preguntas: list[PreguntaPlantillaOpcionMultiple | PreguntaPlantillaVerdaderoFalso]
    total: int
