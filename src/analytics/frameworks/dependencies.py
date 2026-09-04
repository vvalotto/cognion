"""Proveedores de dependencias FastAPI (DI) del BC Analytics.

Composition root del BC — arranca con el puerto de consulta al event store ajeno de Actividad
Evaluativa (`US-4.1.1`). `US-4.1.2` agrega el primer controller y el RBAC de rol `estudiante`,
mismo patrón que `src/actividad_evaluativa/frameworks/dependencies.py`.
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
from src.analytics.interface_adapters.controllers.analytics_controller import (
    AnalyticsController,
)
from src.analytics.use_cases.obtener_desempeno_estudiante import (
    ObtenerDesempenoEstudianteUseCase,
)
from src.shared.entities.ports.jwt_issuer_port import JWTIssuerPort
from src.shared.entities.tipo_perfil import TipoPerfil
from src.shared.frameworks.db import get_session
from src.shared.frameworks.security.jwt_pyjwt import PyJWTIssuer
from src.shared.interface_adapters.security.get_current_user import build_get_current_user
from src.shared.interface_adapters.security.require_rol import require_rol

SessionDep = Annotated[AsyncSession, Depends(get_session)]


def get_evaluacion_desempeno_consulta_port(
    session: SessionDep,
) -> EvaluacionDesempenoConsultaPort:
    """Provee el puerto de consulta de desempeño, cableado contra la sesión async compartida."""
    return EvaluacionDesempenoConsultaPortInProcess(session)


def get_analytics_controller(session: SessionDep) -> AnalyticsController:
    """Arma el `AnalyticsController` con sus dependencias concretas."""
    evaluacion_desempeno_consulta = EvaluacionDesempenoConsultaPortInProcess(session)
    return AnalyticsController(
        ObtenerDesempenoEstudianteUseCase(evaluacion_desempeno_consulta)
    )


def get_jwt_issuer() -> JWTIssuerPort:
    """Provee la implementación de emisor de JWT a usar."""
    return PyJWTIssuer()


get_current_user = build_get_current_user(get_jwt_issuer())
"""Dependency FastAPI que resuelve el usuario autenticado a partir del JWT recibido."""

require_estudiante = require_rol([TipoPerfil.ESTUDIANTE], get_current_user)
"""Dependency que exige rol `estudiante` — consulta del propio desempeño (RF-02, RF-15)."""
