"""Proveedores de dependencias FastAPI (DI) del BC Actividad Evaluativa.

Composition root del BC — arranca con el event store (`US-3.1.1`) y el controller de
actividades (`US-3.1.2`). Próximas US agregan acá sus propios use cases y controllers, mismo
patrón que `src/banco_preguntas/frameworks/dependencies.py`.
"""

from __future__ import annotations

from datetime import timedelta
from typing import Annotated

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from src.actividad_evaluativa.entities.ports.event_store_port import EventStorePort
from src.actividad_evaluativa.frameworks.adapters.estudiante_consulta_port_in_process import (
    EstudianteConsultaPortInProcess,
)
from src.actividad_evaluativa.frameworks.adapters.evaluacion_activa_query_repository import (
    SQLAlchemyEvaluacionActivaQueryRepository,
)
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
from src.actividad_evaluativa.interface_adapters.controllers.evaluaciones_controller import (
    EvaluacionesController,
)
from src.actividad_evaluativa.interface_adapters.controllers.revision_controller import (
    RevisionController,
)
from src.actividad_evaluativa.use_cases.cerrar_actividad import CerrarActividadUseCase
from src.actividad_evaluativa.use_cases.crear_actividad_periodo_abierto import (
    CrearActividadPeriodoAbiertoUseCase,
)
from src.actividad_evaluativa.use_cases.finalizar_evaluacion import FinalizarEvaluacionUseCase
from src.actividad_evaluativa.use_cases.iniciar_evaluacion import IniciarEvaluacionUseCase
from src.actividad_evaluativa.use_cases.modificar_periodo_disponibilidad import (
    ModificarPeriodoDisponibilidadUseCase,
)
from src.actividad_evaluativa.use_cases.obtener_revision_evaluacion import (
    ObtenerRevisionEvaluacionUseCase,
)
from src.actividad_evaluativa.use_cases.reanudar_evaluacion import ReanudarEvaluacionUseCase
from src.actividad_evaluativa.use_cases.registrar_respuesta import RegistrarRespuestaUseCase
from src.actividad_evaluativa.use_cases.suspender_evaluacion import SuspenderEvaluacionUseCase
from src.actividad_evaluativa.use_cases.verificar_vencimientos import (
    VerificarVencimientosUseCase,
)
from src.settings import settings
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
    evaluacion_activa_query = SQLAlchemyEvaluacionActivaQueryRepository(session)
    return ActividadesController(
        CrearActividadPeriodoAbiertoUseCase(materia_consulta, pregunta_consulta, event_store),
        ModificarPeriodoDisponibilidadUseCase(event_store, evaluacion_activa_query),
        CerrarActividadUseCase(
            event_store, evaluacion_activa_query, FinalizarEvaluacionUseCase(event_store)
        ),
    )


def get_jwt_issuer() -> JWTIssuerPort:
    """Provee la implementación de emisor de JWT a usar."""
    return PyJWTIssuer()


get_current_user = build_get_current_user(get_jwt_issuer())
"""Dependency FastAPI que resuelve el usuario autenticado a partir del JWT recibido."""

require_docente = require_rol([TipoPerfil.DOCENTE], get_current_user)
"""Dependency que exige rol `docente` — endpoints de gestión de actividades (RF-02, RF-11)."""

require_estudiante = require_rol([TipoPerfil.ESTUDIANTE], get_current_user)
"""Dependency que exige rol `estudiante` — endpoints de rendición de evaluaciones (RF-02, RF-12)."""


def get_evaluaciones_controller(session: SessionDep) -> EvaluacionesController:
    """Arma el `EvaluacionesController` con sus dependencias concretas."""
    estudiante_consulta = EstudianteConsultaPortInProcess(session)
    pregunta_consulta = PreguntaConsultaPortInProcess(session)
    event_store = SQLAlchemyEventStore(session)
    return EvaluacionesController(
        IniciarEvaluacionUseCase(estudiante_consulta, pregunta_consulta, event_store),
        RegistrarRespuestaUseCase(pregunta_consulta, event_store),
        SuspenderEvaluacionUseCase(event_store),
        ReanudarEvaluacionUseCase(event_store),
        FinalizarEvaluacionUseCase(event_store),
    )


def get_revision_controller(session: SessionDep) -> RevisionController:
    """Arma el `RevisionController` con sus dependencias concretas."""
    pregunta_consulta = PreguntaConsultaPortInProcess(session)
    event_store = SQLAlchemyEventStore(session)
    return RevisionController(ObtenerRevisionEvaluacionUseCase(pregunta_consulta, event_store))


def build_verificar_vencimientos_use_case(session: AsyncSession) -> VerificarVencimientosUseCase:
    """Arma `VerificarVencimientosUseCase` (`US-3.2.4`) con su propia sesión.

    A diferencia del resto de las factories de este módulo, no usa `Annotated[..., Depends]`:
    la Policy corre en un background task (`src/app.py`), fuera del ciclo request/response de
    FastAPI, con una sesión propia por corrida.
    """
    evaluacion_activa_query = SQLAlchemyEvaluacionActivaQueryRepository(session)
    event_store = SQLAlchemyEventStore(session)
    umbral_inactividad = timedelta(
        minutes=settings.verificador_vencimientos_umbral_inactividad_minutos
    )
    return VerificarVencimientosUseCase(
        evaluacion_activa_query,
        event_store,
        SuspenderEvaluacionUseCase(event_store),
        FinalizarEvaluacionUseCase(event_store),
        umbral_inactividad,
    )
