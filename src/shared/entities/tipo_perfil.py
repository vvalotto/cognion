"""Rol de un usuario dentro de la plataforma — transversal a todos los BCs."""

from __future__ import annotations

from enum import StrEnum


class TipoPerfil(StrEnum):
    """Rol de un usuario dentro de la plataforma."""

    ADMINISTRADOR = "administrador"
    DOCENTE = "docente"
    ESTUDIANTE = "estudiante"
