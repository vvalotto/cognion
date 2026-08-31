"""Headers de autorización para los steps BDD de Actividad Evaluativa (`US-3.1.2`/`US-3.1.3`)."""

from __future__ import annotations

import uuid

from src.identidad.entities.comision import Comision
from src.identidad.entities.usuario import Usuario
from src.identidad.frameworks.security.password_hasher import BcryptPasswordHasher
from src.identidad.interface_adapters.gateways.comision_repository import (
    SQLAlchemyComisionRepository,
)
from src.identidad.interface_adapters.gateways.usuario_repository import (
    SQLAlchemyUsuarioRepository,
)
from src.shared.entities.tipo_perfil import TipoPerfil
from src.shared.frameworks.db import SessionLocal
from src.shared.frameworks.security.jwt_pyjwt import PyJWTIssuer


def docente_headers() -> dict[str, str]:
    jwt_vo = PyJWTIssuer().emitir(uuid.uuid4(), TipoPerfil.DOCENTE)
    return {"Authorization": f"Bearer {jwt_vo.token}"}


async def crear_estudiante() -> tuple[str, dict[str, str]]:
    """Crea un `Usuario` real con rol Estudiante y devuelve su id y sus headers de JWT.

    `IniciarEvaluacionUseCase` valida al estudiante contra BC Identidad (`EstudianteConsultaPort`)
    — a diferencia de `docente_headers`, este `estudiante_id` debe existir de verdad en la BD.
    """
    async with SessionLocal() as session:
        hasher = BcryptPasswordHasher()
        usuario_repo = SQLAlchemyUsuarioRepository(session)
        comision_repo = SQLAlchemyComisionRepository(session)

        admin = Usuario.crear(
            "Admin",
            f"admin.{uuid.uuid4()}@fiuner.edu.ar",
            hasher.hash("x"),
            TipoPerfil.ADMINISTRADOR,
        )
        await usuario_repo.guardar(admin)
        comision = Comision.crear(uuid.uuid4(), "lu 10-12", admin.id)
        await comision_repo.guardar(comision)

        estudiante = Usuario.crear_estudiante(
            "Estudiante", f"estudiante.{uuid.uuid4()}@fiuner.edu.ar", hasher.hash("x"), comision.id
        )
        await usuario_repo.guardar(estudiante)

    jwt_vo = PyJWTIssuer().emitir(estudiante.id, TipoPerfil.ESTUDIANTE)
    return str(estudiante.id), {"Authorization": f"Bearer {jwt_vo.token}"}


async def crear_estudiante_de_materia(materia_id: str) -> tuple[str, dict[str, str]]:
    """Como `crear_estudiante()`, pero con `Comision.materia_id` apuntando a una materia real.

    `ListarMateriasDelEstudianteUseCase` (`US-3.4.5`) resuelve esa materia vía `MateriaPort` —
    a diferencia de `IniciarEvaluacionUseCase`, no alcanza con un id aleatorio.
    """
    async with SessionLocal() as session:
        hasher = BcryptPasswordHasher()
        usuario_repo = SQLAlchemyUsuarioRepository(session)
        comision_repo = SQLAlchemyComisionRepository(session)

        admin = Usuario.crear(
            "Admin",
            f"admin.{uuid.uuid4()}@fiuner.edu.ar",
            hasher.hash("x"),
            TipoPerfil.ADMINISTRADOR,
        )
        await usuario_repo.guardar(admin)
        comision = Comision.crear(uuid.UUID(materia_id), "lu 10-12", admin.id)
        await comision_repo.guardar(comision)

        estudiante = Usuario.crear_estudiante(
            "Estudiante", f"estudiante.{uuid.uuid4()}@fiuner.edu.ar", hasher.hash("x"), comision.id
        )
        await usuario_repo.guardar(estudiante)

    jwt_vo = PyJWTIssuer().emitir(estudiante.id, TipoPerfil.ESTUDIANTE)
    return str(estudiante.id), {"Authorization": f"Bearer {jwt_vo.token}"}
