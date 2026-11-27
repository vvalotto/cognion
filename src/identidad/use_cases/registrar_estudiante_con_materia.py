"""Caso de uso: registro de un Estudiante que además devuelve el nombre de su materia."""

from __future__ import annotations

from dataclasses import dataclass
from uuid import UUID

from src.identidad.entities.ports.comision_repository_port import ComisionRepositoryPort
from src.identidad.entities.ports.materia_port import MateriaPort
from src.identidad.entities.usuario import Usuario
from src.identidad.use_cases.registrar_estudiante import RegistrarEstudianteUseCase


@dataclass(frozen=True)
class EstudianteRegistrado:
    """Resultado del registro: el Usuario creado, su comisión y el nombre de la materia."""

    usuario: Usuario
    comision_id: UUID
    materia_nombre: str


class RegistrarEstudianteConMateriaUseCase:
    """Registra al Estudiante con `RegistrarEstudianteUseCase` y resuelve el nombre de su materia."""

    def __init__(
        self,
        registrar_estudiante: RegistrarEstudianteUseCase,
        comision_repositorio: ComisionRepositoryPort,
        materia_port: MateriaPort,
    ) -> None:
        """Recibe el caso de uso de registro y los puertos para resolver el nombre de materia."""
        self._registrar_estudiante = registrar_estudiante
        self._comision_repositorio = comision_repositorio
        self._materia_port = materia_port

    async def execute(
        self, token: str, nombre: str, email: str, password: str
    ) -> EstudianteRegistrado:
        """Delega el registro y resuelve la materia; los errores del registro se propagan."""
        usuario, evento_invitacion, _evento_usuario = await self._registrar_estudiante.execute(
            token, nombre, email, password
        )
        # La comisión y su materia existen siempre en este punto: la invitación no se genera
        # sin una comisión válida (US-1.1.1) y `CrearComisionUseCase` ya validó la materia
        # contra `MateriaPort` al crear la comisión.
        comision = await self._comision_repositorio.obtener_por_id(evento_invitacion.comision_id)
        if comision is None:
            raise LookupError(
                f"Comisión inexistente tras el registro: {evento_invitacion.comision_id}"
            )
        materia = await self._materia_port.obtener(comision.materia_id)
        if materia is None:
            raise LookupError(f"Materia inexistente tras el registro: {comision.materia_id}")
        return EstudianteRegistrado(usuario, comision.id, materia.nombre)
