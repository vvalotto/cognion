"""Proveedores de dependencias (DI) del BC Notificaciones — composition root (`US-5.1.1`).

Arranca con los dos puertos de infraestructura del BC — `CanalEnvioPort` y
`ComisionConsultaPort` — sin controller ni router propios: Notificaciones no expone endpoint
HTTP (BC puramente reactivo, `BC-notificaciones-modelo.md` §2). Estas factories quedan listas
para que los Use Case de `US-5.1.2`/`US-5.1.3` las reciban inyectadas.
"""

from __future__ import annotations

from typing import Annotated

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from src.notificaciones.entities.ports.canal_envio_port import CanalEnvioPort
from src.notificaciones.entities.ports.comision_consulta_port import ComisionConsultaPort
from src.notificaciones.frameworks.adapters.comision_consulta_port_in_process import (
    ComisionConsultaPortInProcess,
)
from src.notificaciones.frameworks.adapters.smtp_canal_envio import SmtpCanalEnvio
from src.shared.frameworks.db import get_session

SessionDep = Annotated[AsyncSession, Depends(get_session)]


def get_canal_envio_port() -> CanalEnvioPort:
    """Provee el canal de envío de notificaciones — `SmtpCanalEnvio` en esta implementación."""
    return SmtpCanalEnvio()


def get_comision_consulta_port(session: SessionDep) -> ComisionConsultaPort:
    """Provee el puerto de consulta de comisiones/destinatarios, cableado contra Identidad."""
    return ComisionConsultaPortInProcess(session)
