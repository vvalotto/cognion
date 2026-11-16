"""Caso de uso: decide si un usuario puede abrir el canal en vivo de una sesión (US-12.1.1)."""

from __future__ import annotations

from uuid import UUID

from src.actividad_evaluativa.entities.actividad_evaluativa_en_vivo import (
    ActividadEvaluativaEnVivo,
)
from src.actividad_evaluativa.entities.ports.comision_consulta_port import ComisionConsultaPort
from src.actividad_evaluativa.entities.ports.estudiante_consulta_port import (
    EstudianteConsultaPort,
)
from src.actividad_evaluativa.entities.ports.event_store_port import EventStorePort
from src.shared.entities.tipo_perfil import TipoPerfil

AGGREGATE_TYPE_SESION = "ActividadEvaluativaEnVivo"


class AutorizarConexionCanalUseCase:
    """Autoriza la conexión al canal según la comisión de la sesión y el rol del usuario."""

    def __init__(
        self,
        event_store: EventStorePort,
        comision_consulta: ComisionConsultaPort,
        estudiante_consulta: EstudianteConsultaPort,
    ) -> None:
        """Recibe el event store y los puertos de consulta de Identidad."""
        self._event_store = event_store
        self._comision_consulta = comision_consulta
        self._estudiante_consulta = estudiante_consulta

    async def execute(self, sesion_id: UUID, usuario_id: UUID, rol: TipoPerfil) -> bool:
        """Devuelve `True` si el usuario pertenece a la comisión de la sesión.

        - Docente: asignado a la comisión de la sesión.
        - Estudiante: su comisión es la de la sesión, aunque todavía no se haya unido.
        - Administrador: siempre, como en el resto de las operaciones de la sesión.

        Una sesión inexistente devuelve `False`, igual que un usuario sin pertenencia: quien
        llama no distingue "no existe" de "no autorizado".
        """
        eventos = await self._event_store.load(AGGREGATE_TYPE_SESION, sesion_id)
        if not eventos:
            return False
        if rol == TipoPerfil.ADMINISTRADOR:
            return True

        comision_id = ActividadEvaluativaEnVivo.reconstruir(eventos).comision_id
        if rol == TipoPerfil.DOCENTE:
            return await self._comision_consulta.esta_asignado_a_comision(usuario_id, comision_id)
        if rol == TipoPerfil.ESTUDIANTE:
            return await self._estudiante_consulta.obtener_comision_id(usuario_id) == comision_id
        return False
