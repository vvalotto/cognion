"""Errores de dominio transversales a todos los BCs (verificación de JWT)."""

from __future__ import annotations


class JWTInvalido(Exception):
    """El token recibido está ausente, malformado o tiene una firma inválida."""

    def __init__(self) -> None:
        """Arma el mensaje genérico de la excepción."""
        super().__init__("Token inválido.")


class JWTExpirado(Exception):
    """El token recibido es válido pero su `exp` ya pasó (ADR-013)."""

    def __init__(self) -> None:
        """Arma el mensaje genérico de la excepción."""
        super().__init__("Token expirado.")
