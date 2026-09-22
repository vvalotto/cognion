"""Caso de uso: listar las sesiones en vivo de una Comisión (US-6.3.2)."""

from __future__ import annotations

from dataclasses import replace
from uuid import UUID

from src.actividad_evaluativa.entities.actividad_evaluativa_en_vivo import EstadoSesionEnVivo
from src.actividad_evaluativa.entities.errors import ComisionNoAutorizada, ComisionRequerida
from src.actividad_evaluativa.entities.ports.estudiante_consulta_port import (
    EstudianteConsultaPort,
)
from src.actividad_evaluativa.entities.ports.materia_consulta_port import MateriaConsultaPort
from src.actividad_evaluativa.entities.ports.sesiones_en_vivo_query_port import (
    SesionesEnVivoQueryPort,
    SesionEnVivoResumen,
)
from src.shared.entities.tipo_perfil import TipoPerfil


class ListarSesionesEnVivoUseCase:
    """Resuelve la Comisión efectiva según el rol y enriquece cada sesión con `materia_nombre`."""

    def __init__(
        self,
        estudiante_consulta: EstudianteConsultaPort,
        sesiones_query: SesionesEnVivoQueryPort,
        materia_consulta: MateriaConsultaPort,
    ) -> None:
        """Recibe las consultas de Identidad, de sesiones y de Banco de Preguntas."""
        self._estudiante_consulta = estudiante_consulta
        self._sesiones_query = sesiones_query
        self._materia_consulta = materia_consulta

    async def execute(
        self,
        usuario_id: UUID,
        rol: TipoPerfil,
        comision_id: UUID | None,
        estados: list[EstadoSesionEnVivo],
    ) -> list[SesionEnVivoResumen]:
        """Devuelve las sesiones visibles para `usuario_id` según su rol.

        Levanta `ComisionRequerida` (Docente sin `comision_id`) o `ComisionNoAutorizada`
        (Estudiante pidiendo una Comisión que no es la propia).
        """
        comision_efectiva = await self._comision_efectiva(usuario_id, rol, comision_id)
        if comision_efectiva is None:
            return []

        sesiones = await self._sesiones_query.listar(comision_efectiva, estados)
        return await self._con_nombre_de_materia(sesiones)

    async def _comision_efectiva(
        self, usuario_id: UUID, rol: TipoPerfil, comision_id: UUID | None
    ) -> UUID | None:
        """Devuelve la Comisión a consultar, o `None` si el Estudiante no cursa ninguna."""
        if rol is TipoPerfil.ESTUDIANTE:
            propia = await self._estudiante_consulta.obtener_comision_id(usuario_id)
            if comision_id is not None and comision_id != propia:
                raise ComisionNoAutorizada(comision_id)
            return propia
        if comision_id is None:
            raise ComisionRequerida()
        return comision_id

    async def _con_nombre_de_materia(
        self, sesiones: list[SesionEnVivoResumen]
    ) -> list[SesionEnVivoResumen]:
        """Resuelve `materia_nombre` por cada `materia_id` único (una sola consulta por lote)."""
        nombres: dict[UUID, str] = {}
        for materia_id in {sesion.materia_id for sesion in sesiones}:
            materia = await self._materia_consulta.obtener(materia_id)
            nombres[materia_id] = materia.nombre if materia is not None else ""
        return [replace(s, materia_nombre=nombres[s.materia_id]) for s in sesiones]
