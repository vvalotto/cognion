"""Adaptador de `NotificacionPort` — llamada in-process a BC Notificaciones (`US-5.1.2`).

Único punto de Actividad Evaluativa que importa `src.notificaciones` — mismo criterio de
acoplamiento consciente (`ADR-006`) que los demás adapters `*_in_process.py` cruzados del
proyecto (`materia_consulta_port_in_process.py`, `evaluacion_consulta_port_in_process.py` de
Identidad). Vive en `frameworks/`, nunca en `entities/` ni `use_cases/`.
"""

from __future__ import annotations

from datetime import datetime
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from src.actividad_evaluativa.entities.ports.notificacion_port import NotificacionPort
from src.notificaciones.frameworks.adapters.comision_consulta_port_in_process import (
    ComisionConsultaPortInProcess,
)
from src.notificaciones.frameworks.adapters.smtp_canal_envio import SmtpCanalEnvio
from src.notificaciones.use_cases.notificar_apertura import NotificarAperturaUseCase
from src.notificaciones.use_cases.notificar_cierre import NotificarCierreUseCase


class NotificacionPortInProcess(NotificacionPort):
    """Implementa `NotificacionPort` invocando los Use Case de Notificaciones in-process."""

    def __init__(self, session: AsyncSession) -> None:
        """Arma internamente los Use Case de Notificaciones con la sesión compartida del request."""
        self._notificar_apertura_use_case = NotificarAperturaUseCase(
            ComisionConsultaPortInProcess(session),
            SmtpCanalEnvio(),
        )
        self._notificar_cierre_use_case = NotificarCierreUseCase(
            ComisionConsultaPortInProcess(session),
            SmtpCanalEnvio(),
        )

    async def notificar_apertura(
        self,
        actividad_id: UUID,
        materia_id: UUID,
        materia_nombre: str,
        titulo: str,
        fecha_apertura: datetime,
        fecha_cierre: datetime,
        comisiones_ids: list[UUID],
    ) -> None:
        """Delega en `NotificarAperturaUseCase` — ver ahí el manejo de fallos de envío."""
        await self._notificar_apertura_use_case.execute(
            actividad_id,
            materia_id,
            materia_nombre,
            titulo,
            fecha_apertura,
            fecha_cierre,
            comisiones_ids,
        )

    async def notificar_cierre(
        self,
        actividad_id: UUID,
        materia_id: UUID,
        materia_nombre: str,
        titulo: str,
        comisiones_ids: list[UUID],
    ) -> None:
        """Delega en `NotificarCierreUseCase` — ver ahí el manejo de fallos de envío."""
        await self._notificar_cierre_use_case.execute(
            actividad_id,
            materia_id,
            materia_nombre,
            titulo,
            comisiones_ids,
        )
