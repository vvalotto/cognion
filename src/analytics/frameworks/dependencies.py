"""Proveedores de dependencias FastAPI (DI) del BC Analytics.

Composition root del BC — arranca con el puerto de consulta al event store ajeno de Actividad
Evaluativa (`US-4.1.1`). Sin controllers todavía: `US-4.1.2` agrega el primero, mismo patrón
que `src/actividad_evaluativa/frameworks/dependencies.py`.
"""

from __future__ import annotations

from typing import Annotated

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from src.analytics.entities.ports.evaluacion_desempeno_consulta_port import (
    EvaluacionDesempenoConsultaPort,
)
from src.analytics.frameworks.adapters.evaluacion_desempeno_consulta_port_in_process import (
    EvaluacionDesempenoConsultaPortInProcess,
)
from src.shared.frameworks.db import get_session

SessionDep = Annotated[AsyncSession, Depends(get_session)]


def get_evaluacion_desempeno_consulta_port(
    session: SessionDep,
) -> EvaluacionDesempenoConsultaPort:
    """Provee el puerto de consulta de desempeño, cableado contra la sesión async compartida."""
    return EvaluacionDesempenoConsultaPortInProcess(session)
