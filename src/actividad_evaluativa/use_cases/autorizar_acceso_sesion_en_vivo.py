"""Caso de uso: exige que un usuario pertenezca a la comisión de una sesión en vivo (US-12.1.2)."""

from __future__ import annotations

from uuid import UUID

from src.actividad_evaluativa.entities.actividad_evaluativa_en_vivo import (
    ActividadEvaluativaEnVivo,
)
from src.actividad_evaluativa.entities.errors import ComisionNoAutorizada, SesionNoExiste
from src.actividad_evaluativa.entities.ports.comision_consulta_port import ComisionConsultaPort
from src.actividad_evaluativa.entities.ports.estudiante_consulta_port import (
    EstudianteConsultaPort,
)
from src.actividad_evaluativa.entities.ports.event_store_port import EventStorePort
from src.shared.entities.tipo_perfil import TipoPerfil

AGGREGATE_TYPE_SESION = "ActividadEvaluativaEnVivo"


class AutorizarAccesoSesionEnVivoUseCase:
    """Regla de pertenencia a la comisión de la sesión, compartida por el canal y los endpoints."""

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

    async def execute(self, sesion_id: UUID, usuario_id: UUID, rol: TipoPerfil) -> None:
        """Verifica que el usuario pertenezca a la comisión de la sesión.

        - Docente: asignado a la comisión de la sesión.
        - Estudiante: su comisión es la de la sesión, aunque todavía no se haya unido.
        - Administrador: siempre.

        Levanta `SesionNoExiste` si la sesión no tiene eventos y `ComisionNoAutorizada` si el
        usuario no pertenece a su comisión (o su rol no tiene regla de pertenencia).
        """
        eventos = await self._event_store.load(AGGREGATE_TYPE_SESION, sesion_id)
        if not eventos:
            raise SesionNoExiste(sesion_id)
        if rol == TipoPerfil.ADMINISTRADOR:
            return

        comision_id = ActividadEvaluativaEnVivo.reconstruir(eventos).comision_id
        if rol == TipoPerfil.DOCENTE:
            pertenece = await self._comision_consulta.esta_asignado_a_comision(
                usuario_id, comision_id
            )
        elif rol == TipoPerfil.ESTUDIANTE:
            pertenece = await self._estudiante_consulta.obtener_comision_id(usuario_id) == (
                comision_id
            )
        else:
            pertenece = False
        if not pertenece:
            raise ComisionNoAutorizada(comision_id)
