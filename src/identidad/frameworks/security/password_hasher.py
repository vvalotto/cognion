"""Implementación de `PasswordHasherPort` con bcrypt (ADR-014)."""

from __future__ import annotations

import bcrypt

from src.identidad.entities.ports.password_hasher_port import PasswordHasherPort


class BcryptPasswordHasher(PasswordHasherPort):
    """Hashea y verifica contraseñas usando bcrypt."""

    def hash(self, password: str) -> str:
        """Genera el hash bcrypt de una contraseña en texto plano."""
        hashed = bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt())
        return hashed.decode("utf-8")

    def verificar(self, password: str, password_hash: str) -> bool:
        """Indica si una contraseña en texto plano corresponde a un hash bcrypt dado."""
        return bcrypt.checkpw(password.encode("utf-8"), password_hash.encode("utf-8"))
