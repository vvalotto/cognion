"""Proveedores de dependencias FastAPI (DI) del BC Identidad."""

from __future__ import annotations

from typing import Annotated

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from src.identidad.entities.ports.jwt_issuer_port import JWTIssuerPort
from src.identidad.entities.ports.notificador_port import NotificadorPort
from src.identidad.entities.ports.password_hasher_port import PasswordHasherPort
from src.identidad.frameworks.security.jwt_pyjwt import PyJWTIssuer
from src.identidad.frameworks.security.password_hasher import BcryptPasswordHasher
from src.identidad.frameworks.smtp.notificador_smtp import SmtpNotificador
from src.identidad.interface_adapters.controllers.auth_controller import AuthController
from src.identidad.interface_adapters.controllers.comisiones_controller import ComisionesController
from src.identidad.interface_adapters.controllers.invitaciones_controller import (
    InvitacionesController,
)
from src.identidad.interface_adapters.controllers.registro_controller import RegistroController
from src.identidad.interface_adapters.controllers.usuarios_controller import UsuariosController
from src.identidad.interface_adapters.gateways.comision_repository import (
    SQLAlchemyComisionRepository,
)
from src.identidad.interface_adapters.gateways.invitacion_repository import (
    SQLAlchemyInvitacionRepository,
)
from src.identidad.interface_adapters.gateways.usuario_repository import SQLAlchemyUsuarioRepository
from src.identidad.use_cases.asignar_docente_a_comision import AsignarDocenteAComisionUseCase
from src.identidad.use_cases.crear_comision import CrearComisionUseCase
from src.identidad.use_cases.crear_usuario import CrearUsuarioUseCase
from src.identidad.use_cases.generar_invitacion import GenerarInvitacionUseCase
from src.identidad.use_cases.iniciar_sesion import IniciarSesionUseCase
from src.identidad.use_cases.registrar_estudiante import RegistrarEstudianteUseCase
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


def get_notificador() -> NotificadorPort:
    """Provee la implementación de notificador de email a usar."""
    return SmtpNotificador()


def get_invitaciones_controller(session: SessionDep) -> InvitacionesController:
    """Arma el `InvitacionesController` con sus dependencias concretas."""
    comision_repo = SQLAlchemyComisionRepository(session)
    invitacion_repo = SQLAlchemyInvitacionRepository(session)
    notificador = get_notificador()
    return InvitacionesController(
        GenerarInvitacionUseCase(comision_repo, invitacion_repo, notificador)
    )


def get_registro_controller(session: SessionDep) -> RegistroController:
    """Arma el `RegistroController` con sus dependencias concretas."""
    invitacion_repo = SQLAlchemyInvitacionRepository(session)
    usuario_repo = SQLAlchemyUsuarioRepository(session)
    hasher = get_password_hasher()
    return RegistroController(RegistrarEstudianteUseCase(invitacion_repo, usuario_repo, hasher))


def get_jwt_issuer() -> JWTIssuerPort:
    """Provee la implementación de emisor de JWT a usar."""
    return PyJWTIssuer()


def get_auth_controller(session: SessionDep) -> AuthController:
    """Arma el `AuthController` con sus dependencias concretas."""
    usuario_repo = SQLAlchemyUsuarioRepository(session)
    hasher = get_password_hasher()
    jwt_issuer = get_jwt_issuer()
    return AuthController(IniciarSesionUseCase(usuario_repo, hasher, jwt_issuer))
