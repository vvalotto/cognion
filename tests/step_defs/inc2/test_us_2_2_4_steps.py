from __future__ import annotations

import asyncio
import uuid

import pytest
from httpx import ASGITransport, AsyncClient
from pytest_bdd import given, parsers, scenarios, then, when
from sqlalchemy import text

from src.app import app
from src.identidad.entities.usuario import Usuario
from src.identidad.frameworks.security.password_hasher import BcryptPasswordHasher
from src.identidad.interface_adapters.gateways.usuario_repository import (
    SQLAlchemyUsuarioRepository,
)
from src.shared.entities.tipo_perfil import TipoPerfil
from src.shared.frameworks.db import SessionLocal
from tests.step_defs.inc1._auth_headers import admin_headers

scenarios("../../features/inc2/US-2.2.4-resetear-password.feature")


def run_async(coro):
    """pytest-bdd no soporta step functions async def — ver ADR-018."""
    return asyncio.run(coro)


async def _limpiar_tablas_identidad() -> None:
    async with SessionLocal() as session:
        await session.execute(text("DELETE FROM invitacion"))
        await session.execute(text("DELETE FROM comision_docentes"))
        await session.execute(text("DELETE FROM estudiante"))
        await session.execute(text("DELETE FROM comision"))
        await session.execute(text("DELETE FROM docente"))
        await session.execute(text("DELETE FROM administrador"))
        await session.execute(text("DELETE FROM usuario"))
        await session.commit()


@pytest.fixture(autouse=True)
def limpiar_tablas_identidad():
    run_async(_limpiar_tablas_identidad())
    yield
    run_async(_limpiar_tablas_identidad())


@pytest.fixture
def context():
    return {}


async def _post(path: str, json: dict):
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        return await client.post(path, json=json, headers=admin_headers())


async def _crear_usuario_con_estado(*, bloqueada: bool) -> uuid.UUID:
    hasher = BcryptPasswordHasher()
    async with SessionLocal() as session:
        repo = SQLAlchemyUsuarioRepository(session)
        email = f"docente.bdd224.{uuid.uuid4()}@fiuner.edu.ar"
        usuario = Usuario.crear("Docente BDD", email, hasher.hash("claveVieja1"), TipoPerfil.DOCENTE)
        await repo.guardar(usuario)
        usuario.bloqueada = bloqueada
        usuario.intentos_fallidos_login = 3 if bloqueada else 0
        usuario.intentos_fallidos_password = 2 if bloqueada else 0
        await repo.actualizar(usuario)
        return usuario.id


async def _obtener_usuario(usuario_id: uuid.UUID) -> Usuario:
    async with SessionLocal() as session:
        repo = SQLAlchemyUsuarioRepository(session)
        usuario = await repo.obtener_por_id(usuario_id)
        assert usuario is not None
        return usuario


@given("un Usuario con bloqueada = true")
def usuario_bloqueado(context):
    usuario_id = run_async(_crear_usuario_con_estado(bloqueada=True))
    usuario = run_async(_obtener_usuario(usuario_id))
    context["usuario_id"] = usuario_id
    context["password_hash_original"] = usuario.password_hash


@given("un Usuario con bloqueada = false")
def usuario_activo(context):
    usuario_id = run_async(_crear_usuario_con_estado(bloqueada=False))
    usuario = run_async(_obtener_usuario(usuario_id))
    context["usuario_id"] = usuario_id
    context["password_hash_original"] = usuario.password_hash


@given("un Usuario existente")
def usuario_existente(context):
    usuario_id = run_async(_crear_usuario_con_estado(bloqueada=False))
    usuario = run_async(_obtener_usuario(usuario_id))
    context["usuario_id"] = usuario_id
    context["password_hash_original"] = usuario.password_hash


@when(
    parsers.parse(
        'un Administrador ejecuta ResetearPassword(usuario_id, "{password_nueva}", administrador_id)'
    )
)
def ejecuta_resetear_password(context, password_nueva):
    context["response"] = run_async(
        _post(
            f"/usuarios/{context['usuario_id']}/resetear-password",
            {"password_nueva": password_nueva},
        )
    )


@then("el sistema actualiza password_hash")
def valida_actualiza_password_hash(context):
    assert context["response"].status_code == 200
    usuario = run_async(_obtener_usuario(context["usuario_id"]))
    assert usuario.password_hash != context["password_hash_original"]


@then("bloqueada pasa a false, los contadores vuelven a 0")
def valida_desbloqueo_y_contadores(context):
    usuario = run_async(_obtener_usuario(context["usuario_id"]))
    assert usuario.bloqueada is False
    assert usuario.intentos_fallidos_login == 0
    assert usuario.intentos_fallidos_password == 0


@then("se emiten PasswordReseteada y CuentaDesbloqueada")
def valida_eventos_password_y_desbloqueo(context):
    # Sin event store en el proyecto (mismo criterio que US-2.2.1): se verifica el efecto
    # observable (desbloqueo) acá y la emisión de ambos eventos en
    # `tests/unit/inc1/test_resetear_password_use_case.py`.
    usuario = run_async(_obtener_usuario(context["usuario_id"]))
    assert usuario.bloqueada is False


@then("se emite PasswordReseteada, sin CuentaDesbloqueada")
def valida_evento_solo_password_reseteada(context):
    usuario = run_async(_obtener_usuario(context["usuario_id"]))
    assert usuario.bloqueada is False
    assert context["response"].status_code == 200


@then("el sistema rechaza con PasswordDemasiadoCorta")
def valida_rechazo_password_demasiado_corta(context):
    assert context["response"].status_code == 422
    usuario = run_async(_obtener_usuario(context["usuario_id"]))
    assert usuario.password_hash == context["password_hash_original"]
