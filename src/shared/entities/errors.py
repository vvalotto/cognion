"""Errores de dominio: la base común, sus cinco categorías y los errores transversales (`ADR-029`).

Todo error de dominio hereda de `ErrorDeDominio` a través de **una** de las categorías. La categoría
dice qué clase de problema es; qué código HTTP le corresponde lo decide `frameworks/` en un solo
lugar (`shared/frameworks/api/errores.py`), de modo que el dominio no conoce HTTP.
"""

from __future__ import annotations

from typing import Any, ClassVar


class ErrorDeDominio(Exception):
    """Base de todos los errores de dominio.

    `codigo` es opcional: si el error lo define, su `detalle()` es el objeto `{codigo, mensaje}`
    que el frontend lee para no interpretar el texto; si no, es el texto del error.
    """

    codigo: ClassVar[str | None] = None

    def detalle(self) -> str | dict[str, Any]:
        """Cuerpo del `detail` de la respuesta de error."""
        if self.codigo is None:
            return str(self)
        return {"codigo": self.codigo, "mensaje": str(self)}


class NoEncontrado(ErrorDeDominio):
    """El recurso pedido no existe."""


class NoAutorizado(ErrorDeDominio):
    """El usuario está autenticado pero no puede hacer esto."""


class NoAutenticado(ErrorDeDominio):
    """No se pudo comprobar quién es el usuario (credenciales o token inválidos)."""


class ReglaViolada(ErrorDeDominio):
    """El pedido viola una regla de negocio o un dato es inválido."""


class Conflicto(ErrorDeDominio):
    """El pedido choca con el estado actual (duplicado, concurrencia)."""


class JWTInvalido(NoAutenticado):
    """El token recibido está ausente, malformado o tiene una firma inválida."""

    def __init__(self) -> None:
        """Arma el mensaje genérico de la excepción."""
        super().__init__("Token inválido.")


class JWTExpirado(NoAutenticado):
    """El token recibido es válido pero su `exp` ya pasó (ADR-013)."""

    def __init__(self) -> None:
        """Arma el mensaje genérico de la excepción."""
        super().__init__("Token expirado.")
