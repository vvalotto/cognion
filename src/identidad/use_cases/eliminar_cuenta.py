"""Caso de uso: baja de una cuenta — física si no tiene datos asociados, lógica si tiene."""

from __future__ import annotations

from uuid import UUID

from src.identidad.entities.errors import UsuarioNoExiste
from src.identidad.entities.ports.comision_query_port import ComisionQueryPort
from src.identidad.entities.ports.evaluacion_consulta_port import EvaluacionConsultaPort
from src.identidad.entities.ports.usuario_repository_port import UsuarioRepositoryPort
from src.identidad.entities.usuario import Administrador, Docente, Estudiante, Usuario


class EliminarCuentaUseCase:
    """Da de baja una cuenta: física si no tiene datos asociados, lógica si tiene.

    Docente con Comisiones asignadas, Estudiante con evaluaciones rendidas, o Administrador
    que creó alguna Comisión → deshabilita (`deshabilitada=True`, distinto de `bloqueada`).
    El caso del Administrador no lo pidió Víctor explícitamente, pero
    `comision.administrador_id` es `NOT NULL` sin `ON DELETE CASCADE` — borrarlo sin este
    chequeo rompería esa FK.
    """

    def __init__(
        self,
        usuario_repositorio: UsuarioRepositoryPort,
        comision_query: ComisionQueryPort,
        evaluacion_consulta: EvaluacionConsultaPort,
    ) -> None:
        """Recibe el repositorio de usuarios y los puertos de consulta a usar."""
        self._usuario_repositorio = usuario_repositorio
        self._comision_query = comision_query
        self._evaluacion_consulta = evaluacion_consulta

    async def execute(self, usuario_id: UUID) -> Usuario | None:
        """Elimina o deshabilita `usuario_id` según tenga datos asociados.

        Devuelve el `Usuario` deshabilitado si se optó por baja lógica, o `None` si se
        eliminó físicamente. Lanza `UsuarioNoExiste` si la cuenta no existe.
        """
        usuario = await self._usuario_repositorio.obtener_por_id(usuario_id)
        if usuario is None:
            raise UsuarioNoExiste(usuario_id)

        tiene_datos_asociados = False
        if isinstance(usuario.perfil, Docente):
            tiene_datos_asociados = await self._comision_query.tiene_comisiones_asignadas(
                usuario_id
            )
        elif isinstance(usuario.perfil, Estudiante):
            tiene_datos_asociados = await self._evaluacion_consulta.tiene_evaluaciones(
                usuario_id
            )
        elif isinstance(usuario.perfil, Administrador):
            tiene_datos_asociados = await self._comision_query.tiene_comisiones_creadas(
                usuario_id
            )

        if tiene_datos_asociados:
            usuario.deshabilitar()
            await self._usuario_repositorio.actualizar(usuario)
            return usuario

        await self._usuario_repositorio.eliminar(usuario_id)
        return None
