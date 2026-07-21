from __future__ import annotations

import bcrypt

from src.identidad.entities.ports.password_hasher_port import PasswordHasherPort


class BcryptPasswordHasher(PasswordHasherPort):
    def hash(self, password: str) -> str:
        hashed = bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt())
        return hashed.decode("utf-8")

    def verificar(self, password: str, password_hash: str) -> bool:
        return bcrypt.checkpw(password.encode("utf-8"), password_hash.encode("utf-8"))
