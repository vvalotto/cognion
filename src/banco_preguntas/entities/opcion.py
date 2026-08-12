"""Opción de una pregunta de opción múltiple."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Opcion:
    """Una opción de respuesta, correcta o no."""

    texto: str
    es_correcta: bool
