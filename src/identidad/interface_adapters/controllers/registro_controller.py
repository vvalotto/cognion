"""Controller de la API para el registro de Estudiantes vía invitación."""

from __future__ import annotations

from src.identidad.interface_adapters.presenters.identidad_presenter import (
    RegistroSalida,
    presentar_registro,
)
from src.identidad.use_cases.registrar_estudiante_con_materia import (
    RegistrarEstudianteConMateriaUseCase,
)


class RegistroController:
    """Adapta requests HTTP al caso de uso de registro de Estudiantes."""

    def __init__(self, registrar_estudiante: RegistrarEstudianteConMateriaUseCase) -> None:
        """Recibe el caso de uso de registro, que también resuelve el nombre de la materia."""
        self._registrar_estudiante = registrar_estudiante

    async def registrar_estudiante(
        self, token: str, nombre: str, email: str, password: str
    ) -> RegistroSalida:
        """Registra al Estudiante y presenta el resultado."""
        registrado = await self._registrar_estudiante.execute(token, nombre, email, password)
        return presentar_registro(registrado)
