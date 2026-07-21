from __future__ import annotations

from uuid import UUID


class EmailYaRegistrado(Exception):
    def __init__(self, email: str) -> None:
        self.email = email
        super().__init__(f"El email '{email}' ya está registrado.")


class UsuarioNoEsDocente(Exception):
    def __init__(self, usuario_id: UUID) -> None:
        self.usuario_id = usuario_id
        super().__init__(f"El usuario '{usuario_id}' no tiene perfil Docente.")


class ComisionNoExiste(Exception):
    def __init__(self, comision_id: UUID) -> None:
        self.comision_id = comision_id
        super().__init__(f"La comisión '{comision_id}' no existe.")
