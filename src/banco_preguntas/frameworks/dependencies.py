"""Proveedores de dependencias FastAPI (DI) del BC Banco de Preguntas."""

from __future__ import annotations

from typing import Annotated

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from src.banco_preguntas.interface_adapters.controllers.materias_controller import (
    MateriasController,
)
from src.banco_preguntas.interface_adapters.controllers.preguntas_controller import (
    PreguntasController,
)
from src.banco_preguntas.interface_adapters.gateways.banco_repository import (
    SQLAlchemyBancoRepository,
)
from src.banco_preguntas.interface_adapters.gateways.materia_repository import (
    SQLAlchemyMateriaRepository,
)
from src.banco_preguntas.interface_adapters.gateways.pregunta_repository import (
    SQLAlchemyPreguntaRepository,
)
from src.banco_preguntas.use_cases.cargar_pregunta_opcion_multiple import (
    CargarPreguntaOpcionMultipleUseCase,
)
from src.banco_preguntas.use_cases.cargar_pregunta_verdadero_falso import (
    CargarPreguntaVerdaderoFalsoUseCase,
)
from src.banco_preguntas.use_cases.crear_materia import CrearMateriaUseCase
from src.banco_preguntas.use_cases.editar_pregunta import EditarPreguntaUseCase
from src.shared.entities.ports.jwt_issuer_port import JWTIssuerPort
from src.shared.entities.tipo_perfil import TipoPerfil
from src.shared.frameworks.db import get_session
from src.shared.frameworks.security.jwt_pyjwt import PyJWTIssuer
from src.shared.interface_adapters.security.get_current_user import build_get_current_user
from src.shared.interface_adapters.security.require_rol import require_rol

SessionDep = Annotated[AsyncSession, Depends(get_session)]


def get_materias_controller(session: SessionDep) -> MateriasController:
    """Arma el `MateriasController` con sus dependencias concretas."""
    materia_repo = SQLAlchemyMateriaRepository(session)
    banco_repo = SQLAlchemyBancoRepository(session)
    return MateriasController(CrearMateriaUseCase(materia_repo, banco_repo))


def get_preguntas_controller(session: SessionDep) -> PreguntasController:
    """Arma el `PreguntasController` con sus dependencias concretas."""
    banco_repo = SQLAlchemyBancoRepository(session)
    pregunta_repo = SQLAlchemyPreguntaRepository(session)
    return PreguntasController(
        CargarPreguntaOpcionMultipleUseCase(banco_repo, pregunta_repo),
        CargarPreguntaVerdaderoFalsoUseCase(banco_repo, pregunta_repo),
        EditarPreguntaUseCase(pregunta_repo),
    )


def get_jwt_issuer() -> JWTIssuerPort:
    """Provee la implementación de emisor de JWT a usar."""
    return PyJWTIssuer()


get_current_user = build_get_current_user(get_jwt_issuer())
"""Dependency FastAPI que resuelve el usuario autenticado a partir del JWT recibido."""

require_docente = require_rol([TipoPerfil.DOCENTE], get_current_user)
"""Dependency que exige rol `docente` — endpoints de gestión del banco de preguntas (RF-02)."""
