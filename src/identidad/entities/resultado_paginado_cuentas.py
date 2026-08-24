"""Resultado paginado de una consulta de cuentas (US-ADJ-05)."""

from __future__ import annotations

from dataclasses import dataclass

from src.identidad.entities.usuario import Usuario


@dataclass(frozen=True)
class ResultadoPaginadoCuentas:
    """Página de cuentas junto con el total que matchea los filtros, sin paginar."""

    cuentas: list[Usuario]
    total: int
