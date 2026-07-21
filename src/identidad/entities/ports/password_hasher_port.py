from abc import ABC, abstractmethod


class PasswordHasherPort(ABC):
    @abstractmethod
    def hash(self, password: str) -> str: ...

    @abstractmethod
    def verificar(self, password: str, password_hash: str) -> bool: ...
