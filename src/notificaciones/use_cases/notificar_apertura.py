"""Caso de uso: notificación de apertura de una Actividad Evaluativa (US-5.1.2, RF-14)."""

from __future__ import annotations

import logging
from datetime import datetime
from uuid import UUID

from src.notificaciones.entities.ports.canal_envio_port import CanalEnvioPort
from src.notificaciones.entities.ports.comision_consulta_port import ComisionConsultaPort

logger = logging.getLogger(__name__)


class NotificarAperturaUseCase:
    """Resuelve destinatarios y envía el email de apertura de una actividad de período abierto.

    Nunca lanza — quien lo invoca (`NotificacionPortInProcess` de Actividad Evaluativa) no
    puede ver propagada ninguna excepción de este BC (`BC-notificaciones-modelo.md` §5/§6).
    """

    def __init__(
        self, comision_consulta: ComisionConsultaPort, canal_envio: CanalEnvioPort
    ) -> None:
        """Recibe el puerto de resolución de destinatarios y el canal de envío de email."""
        self._comision_consulta = comision_consulta
        self._canal_envio = canal_envio

    async def execute(
        self,
        actividad_id: UUID,
        materia_id: UUID,
        materia_nombre: str,
        titulo: str,
        fecha_apertura: datetime,
        fecha_cierre: datetime,
        comisiones_ids: list[UUID],
    ) -> None:
        """Envía un email a cada destinatario del roster resuelto para la actividad.

        `comisiones_ids` no vacío restringe el roster a esas comisiones; vacío resuelve todas
        las comisiones activas de la materia. Materia sin ninguna comisión → sin destinatarios,
        sin invocar `listar_destinatarios`. Un fallo de envío a un destinatario se loguea y no
        aborta el resto del roster (`actividad_id` se incluye solo en el log de fallo, no en el
        contenido del email).
        """
        if comisiones_ids:
            destinatarios = await self._comision_consulta.listar_destinatarios(comisiones_ids)
        else:
            comisiones_materia = await self._comision_consulta.listar_comisiones_por_materia(
                materia_id
            )
            if not comisiones_materia:
                return
            destinatarios = await self._comision_consulta.listar_destinatarios(
                comisiones_materia
            )

        asunto = f"Nueva actividad disponible: {titulo}"
        cuerpo = (
            "Se abrió una nueva actividad de evaluación.\n\n"
            f"Materia: {materia_nombre}\n"
            f"Título: {titulo}\n"
            f"Apertura: {fecha_apertura.isoformat()}\n"
            f"Cierre: {fecha_cierre.isoformat()}\n"
        )

        for destinatario in destinatarios:
            try:
                await self._canal_envio.enviar(destinatario.email, asunto, cuerpo)
            except Exception:  # pylint: disable=broad-except
                logger.warning(
                    "Fallo al enviar notificación de apertura de actividad %s a "
                    "estudiante %s (%s)",
                    actividad_id,
                    destinatario.estudiante_id,
                    destinatario.email,
                    exc_info=True,
                )
