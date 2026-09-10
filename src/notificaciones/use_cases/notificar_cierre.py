"""Caso de uso: notificación de cierre manual de una Actividad Evaluativa (US-5.1.3, RF-14)."""

from __future__ import annotations

import logging
from uuid import UUID

from src.notificaciones.entities.ports.canal_envio_port import CanalEnvioPort
from src.notificaciones.entities.ports.comision_consulta_port import ComisionConsultaPort

logger = logging.getLogger(__name__)


class NotificarCierreUseCase:
    """Resuelve destinatarios y envía el email de cierre manual de una actividad.

    Nunca lanza — mismo criterio que `NotificarAperturaUseCase` (`US-5.1.2`): quien lo invoca
    (`NotificacionPortInProcess` de Actividad Evaluativa) no puede ver propagada ninguna
    excepción de este BC (`BC-notificaciones-modelo.md` §5/§6).
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
        comisiones_ids: list[UUID],
    ) -> None:
        """Envía un email a cada destinatario del roster resuelto para la actividad cerrada.

        Mismo criterio de resolución de roster que `NotificarAperturaUseCase.execute()`:
        `comisiones_ids` no vacío restringe a esas comisiones; vacío resuelve todas las
        comisiones activas de la materia (materia sin ninguna → sin destinatarios). Un fallo de
        envío a un destinatario se loguea y no aborta el resto del roster.
        """
        if comisiones_ids:
            destinatarios = await self._comision_consulta.listar_destinatarios(comisiones_ids)
        else:
            comisiones_materia = await self._comision_consulta.listar_comisiones_por_materia(
                materia_id
            )
            if not comisiones_materia:
                return
            destinatarios = await self._comision_consulta.listar_destinatarios(comisiones_materia)

        asunto = f"Actividad cerrada: {titulo}"
        cuerpo = (
            "Se cerró la siguiente actividad de evaluación. Ya no está disponible para "
            "rendir.\n\n"
            f"Materia: {materia_nombre}\n"
            f"Título: {titulo}\n"
        )

        for destinatario in destinatarios:
            try:
                await self._canal_envio.enviar(destinatario.email, asunto, cuerpo)
            except Exception:  # pylint: disable=broad-except
                logger.warning(
                    "Fallo al enviar notificación de cierre de actividad %s a "
                    "estudiante %s (%s)",
                    actividad_id,
                    destinatario.estudiante_id,
                    destinatario.email,
                    exc_info=True,
                )
