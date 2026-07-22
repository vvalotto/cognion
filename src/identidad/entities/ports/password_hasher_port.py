"""Puerto de hashing y verificación de contraseñas."""

from abc import ABC, abstractmethod


class PasswordHasherPort(ABC):
    """Operaciones requeridas para manejar contraseñas de forma segura."""

    @abstractmethod
    def hash(self, password: str) -> str:
        """Genera el hash de una contraseña en texto plano."""
        ...

    @abstractmethod
    def verificar(self, password: str, password_hash: str) -> bool:
        """Indica si una contraseña en texto plano corresponde a un hash dado."""
        ...
