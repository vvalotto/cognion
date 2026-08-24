"""Nivel de importancia de una pregunta — metadato de clasificación (RF-06)."""

from __future__ import annotations

from enum import StrEnum


class Importancia(StrEnum):
    """Importancia de una pregunta."""

    ALTO = "alto"
    MEDIO = "medio"
    BAJO = "bajo"
