"""Nivel de dificultad de una pregunta — metadato de clasificación (RF-06)."""

from __future__ import annotations

from enum import StrEnum


class Dificultad(StrEnum):
    """Dificultad de una pregunta."""

    ALTO = "alto"
    MEDIO = "medio"
    BAJO = "bajo"
