"""Proveedores de dependencias FastAPI (DI) del BC Actividad Evaluativa.

Composition root del BC — arranca con el event store (`US-3.1.1`) y el controller de
actividades (`US-3.1.2`). Próximas US agregan acá sus propios use cases y controllers, mismo
patrón que `src/banco_preguntas/frameworks/dependencies.py`.
"""

from __future__ import annotations

from typing import Annotated

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from src.actividad_evaluativa.entities.ports.event_store_port import EventStorePort
from src.actividad_evaluativa.frameworks.adapters.materia_consulta_port_in_process import (
    MateriaConsultaPortInProcess,
)
from src.actividad_evaluativa.frameworks.adapters.pregunta_consulta_port_in_process import (
    PreguntaConsultaPortInProcess,
)
from src.actividad_evaluativa.frameworks.event_store.sqlalchemy_event_store import (
    SQLAlchemyEventStore,
)
from src.actividad_evaluativa.interface_adapters.controllers.actividades_controller import (
    ActividadesController,
)
from src.actividad_evaluativa.use_cases.crear_actividad_periodo_abierto import (
    CrearActividadPeriodoAbiertoUseCase,
)
from src.shared.entities.ports.jwt_issuer_port import JWTIssuerPort
from src.shared.entities.tipo_perfil import TipoPerfil
from src.shared.frameworks.db import get_session
from src.shared.frameworks.security.jwt_pyjwt import PyJWTIssuer
from src.shared.interface_adapters.security.get_current_user import build_get_current_user
from src.shared.interface_adapters.security.require_rol import require_rol

SessionDep = Annotated[AsyncSession, Depends(get_session)]


def get_event_store(session: SessionDep) -> EventStorePort:
    """Provee la implementación concreta del event store del BC."""
    return SQLAlchemyEventStore(session)


def get_actividades_controller(session: SessionDep) -> ActividadesController:
    """Arma el `ActividadesController` con sus dependencias concretas."""
    materia_consulta = MateriaConsultaPortInProcess(session)
    pregunta_consulta = PreguntaConsultaPortInProcess(session)
    event_store = SQLAlchemyEventStore(session)
    return ActividadesController(
        CrearActividadPeriodoAbiertoUseCase(materia_consulta, pregunta_consulta, event_store)
    )


def get_jwt_issuer() -> JWTIssuerPort:
    """Provee la implementación de emisor de JWT a usar."""
    return PyJWTIssuer()


get_current_user = build_get_current_user(get_jwt_issuer())
"""Dependency FastAPI que resuelve el usuario autenticado a partir del JWT recibido."""

require_docente = require_rol([TipoPerfil.DOCENTE], get_current_user)
"""Dependency que exige rol `docente` — endpoints de gestión de actividades (RF-02, RF-11)."""
