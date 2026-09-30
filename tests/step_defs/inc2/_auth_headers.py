"""Headers de autorización para los steps BDD de Banco de Preguntas (`US-2.1.1`)."""

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


def admin_headers() -> dict[str, str]:
    jwt_vo = PyJWTIssuer().emitir(uuid.uuid4(), TipoPerfil.ADMINISTRADOR)
    return {"Authorization": f"Bearer {jwt_vo.token}"}


async def docente_asignado_a_materia(materia_id: str) -> tuple[str, dict[str, str]]:
    """Crea un Docente real, una Comisión de `materia_id` y lo asigna (`US-ADJ-57`).

    A diferencia de `docente_headers()`, `Comision.actualizar()` exige una fila `DocenteModel`
    real para persistir la asignación (relación ORM, no INSERT directo) — no alcanza con un
    id de JWT anónimo. Un Administrador dummy es el dueño de la Comisión (`Comision.crear`).
    """
    async with SessionLocal() as session:
        usuario_repo = SQLAlchemyUsuarioRepository(session)
        comision_repo = SQLAlchemyComisionRepository(session)
        hasher = BcryptPasswordHasher()

        admin = Usuario.crear(
            "Admin",
            f"admin.{uuid.uuid4()}@fiuner.edu.ar",
            hasher.hash("x"),
            TipoPerfil.ADMINISTRADOR,
        )
        await usuario_repo.guardar(admin)
        docente = Usuario.crear(
            "Docente", f"docente.{uuid.uuid4()}@fiuner.edu.ar", hasher.hash("x"), TipoPerfil.DOCENTE
        )
        await usuario_repo.guardar(docente)

        comision = Comision.crear(uuid.UUID(materia_id), "lu 10-12", admin.id)
        await comision_repo.guardar(comision)
        comision.asignar_docente(docente.id)
        await comision_repo.actualizar(comision)

    jwt_vo = PyJWTIssuer().emitir(docente.id, TipoPerfil.DOCENTE)
    return str(docente.id), {"Authorization": f"Bearer {jwt_vo.token}"}
