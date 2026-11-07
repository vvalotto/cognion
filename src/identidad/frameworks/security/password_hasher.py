"""Implementación de `PasswordHasherPort` con bcrypt (ADR-014, US-ADJ-63)."""

from __future__ import annotations

import asyncio
import os
from concurrent.futures import ThreadPoolExecutor
from functools import lru_cache

import bcrypt

from src.identidad.entities.ports.password_hasher_port import PasswordHasherPort


@lru_cache(maxsize=1)
def _ejecutor_de_bcrypt() -> ThreadPoolExecutor:
    """Ejecutor propio de bcrypt, acotado a la cantidad de núcleos y creado la primera vez.

    bcrypt libera el GIL, así que varios hilos aprovechan varios núcleos. Acotarlo a
    `os.cpu_count()` evita que una ráfaga de logins deje sin CPU al hilo del event loop, que es lo
    que se busca no bloquear (`US-ADJ-63`).
    """
    return ThreadPoolExecutor(max_workers=os.cpu_count() or 1, thread_name_prefix="bcrypt")


class BcryptPasswordHasher(PasswordHasherPort):
    """Hashea y verifica contraseñas usando bcrypt.

    `hash`/`verificar` son síncronos y bloquean el hilo que los llama: sirven para sembrar datos o
    para herramientas fuera del event loop. Los casos de uso usan `hash_async`/`verificar_async`.
    """

    def hash(self, password: str) -> str:
        """Genera el hash bcrypt de una contraseña en texto plano."""
        hashed = bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt())
        return hashed.decode("utf-8")

    def verificar(self, password: str, password_hash: str) -> bool:
        """Indica si una contraseña en texto plano corresponde a un hash bcrypt dado."""
        return bcrypt.checkpw(password.encode("utf-8"), password_hash.encode("utf-8"))

    async def hash_async(self, password: str) -> str:
        """Genera el hash bcrypt en un hilo, sin bloquear el event loop."""
        return await asyncio.get_running_loop().run_in_executor(
            _ejecutor_de_bcrypt(), self.hash, password
        )

    async def verificar_async(self, password: str, password_hash: str) -> bool:
        """Verifica la contraseña contra el hash bcrypt en un hilo, sin bloquear el event loop."""
        return await asyncio.get_running_loop().run_in_executor(
            _ejecutor_de_bcrypt(), self.verificar, password, password_hash
        )
