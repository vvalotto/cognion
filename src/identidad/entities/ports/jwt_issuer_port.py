"""Puerto de emisión de tokens de sesión (JWT)."""

from __future__ import annotations

from abc import ABC, abstractmethod
from uuid import UUID

from src.identidad.entities.jwt import JWT
from src.identidad.entities.usuario import TipoPerfil


class JWTIssuerPort(ABC):
    """Operaciones requeridas para emitir un token de sesión."""

    @abstractmethod
    def emitir(self, usuario_id: UUID, rol: TipoPerfil) -> JWT:
        """Genera un `JWT` con claim `rol` para el usuario dado (ADR-007, ADR-013)."""
        ...
