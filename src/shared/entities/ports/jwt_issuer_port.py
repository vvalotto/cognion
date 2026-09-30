"""Puerto de emisión y verificación de tokens de sesión (JWT)."""

from __future__ import annotations

from abc import ABC, abstractmethod
from uuid import UUID

from src.shared.entities.jwt import JWT, JWTPayload
from src.shared.entities.tipo_perfil import TipoPerfil


class JWTIssuerPort(ABC):
    """Operaciones requeridas para emitir y verificar un token de sesión."""

    @abstractmethod
    def emitir(self, usuario_id: UUID, rol: TipoPerfil, nombre: str = "") -> JWT:
        """Genera un `JWT` con claims `rol` y `nombre` para el usuario dado (ADR-007, ADR-013)."""

    @abstractmethod
    def verificar(self, token: str) -> JWTPayload:
        """Decodifica y valida `token`; levanta `JWTInvalido`/`JWTExpirado` si no es válido."""
