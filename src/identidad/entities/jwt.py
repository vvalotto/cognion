"""Value Object del token de sesión emitido tras una autenticación exitosa."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from src.identidad.entities.usuario import TipoPerfil


@dataclass(frozen=True)
class JWT:
    """Token de sesión con el rol del `Usuario` autenticado y su expiración (ADR-013)."""

    token: str
    rol: TipoPerfil
    expira_en: datetime
