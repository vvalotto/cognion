"""Puerto de hashing y verificación de contraseñas."""

from abc import ABC, abstractmethod


class PasswordHasherPort(ABC):
    """Operaciones requeridas para manejar contraseñas de forma segura."""

    @abstractmethod
    def hash(self, password: str) -> str:
        """Genera el hash de una contraseña en texto plano."""

    @abstractmethod
    def verificar(self, password: str, password_hash: str) -> bool:
        """Indica si una contraseña en texto plano corresponde a un hash dado."""

    @abstractmethod
    async def hash_async(self, password: str) -> str:
        """Genera el hash de una contraseña sin bloquear el event loop (`US-ADJ-63`).

        Es la forma que usan los casos de uso: bcrypt tarda cientos de milisegundos y, ejecutado
        en el hilo del event loop, congela toda la aplicación (incluidos los WebSockets).
        """

    @abstractmethod
    async def verificar_async(self, password: str, password_hash: str) -> bool:
        """Indica si una contraseña corresponde a un hash, sin bloquear el event loop."""
