"""Proveedores de dependencias FastAPI (DI) del BC Identidad."""

from __future__ import annotations

from typing import Annotated

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from src.identidad.entities.ports.password_hasher_port import PasswordHasherPort
from src.identidad.frameworks.security.password_hasher import BcryptPasswordHasher
from src.identidad.interface_adapters.controllers.comisiones_controller import ComisionesController
from src.identidad.interface_adapters.controllers.usuarios_controller import UsuariosController
from src.identidad.interface_adapters.gateways.comision_repository import (
    SQLAlchemyComisionRepository,
)
from src.identidad.interface_adapters.gateways.usuario_repository import SQLAlchemyUsuarioRepository
from src.identidad.use_cases.asignar_docente_a_comision import AsignarDocenteAComisionUseCase
from src.identidad.use_cases.crear_comision import CrearComisionUseCase
from src.identidad.use_cases.crear_usuario import CrearUsuarioUseCase
from src.shared.frameworks.db import get_session

SessionDep = Annotated[AsyncSession, Depends(get_session)]


def get_password_hasher() -> PasswordHasherPort:
    """Provee la implementación de hasher de contraseñas a usar."""
    return BcryptPasswordHasher()


def get_usuarios_controller(session: SessionDep) -> UsuariosController:
    """Arma el `UsuariosController` con sus dependencias concretas."""
    repo = SQLAlchemyUsuarioRepository(session)
    hasher = get_password_hasher()
    return UsuariosController(CrearUsuarioUseCase(repo, hasher))


def get_comisiones_controller(session: SessionDep) -> ComisionesController:
    """Arma el `ComisionesController` con sus dependencias concretas."""
    comision_repo = SQLAlchemyComisionRepository(session)
    usuario_repo = SQLAlchemyUsuarioRepository(session)
    return ComisionesController(
        CrearComisionUseCase(comision_repo),
        AsignarDocenteAComisionUseCase(comision_repo, usuario_repo),
    )
