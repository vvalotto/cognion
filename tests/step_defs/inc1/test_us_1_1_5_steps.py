from __future__ import annotations

import asyncio
import uuid
from datetime import UTC, datetime, timedelta

import jwt as pyjwt
import pytest
from httpx import ASGITransport, AsyncClient
from pytest_bdd import given, parsers, scenarios, then, when
from sqlalchemy import text

from src.app import app
from src.identidad.entities.usuario import TipoPerfil
from src.identidad.frameworks.security.jwt_pyjwt import PyJWTIssuer
from src.settings import settings
from src.shared.frameworks.db import SessionLocal

scenarios("../../features/inc1/US-1.1.5-autorizacion-rbac.feature")


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


_ROL_A_TIPO = {
    "administrador": TipoPerfil.ADMINISTRADOR,
    "docente": TipoPerfil.DOCENTE,
    "estudiante": TipoPerfil.ESTUDIANTE,
}


def _token_valido(rol: str) -> str:
    return PyJWTIssuer().emitir(uuid.uuid4(), _ROL_A_TIPO[rol]).token


def _token_expirado(rol: str) -> str:
    payload = {
        "sub": str(uuid.uuid4()),
        "rol": _ROL_A_TIPO[rol].value,
        "exp": datetime.now(UTC) - timedelta(minutes=1),
    }
    return pyjwt.encode(payload, settings.secret_key, algorithm=settings.algorithm)


async def _post(path: str, json: dict, headers: dict[str, str] | None = None):
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        return await client.post(path, json=json, headers=headers)


def _body_crear_usuario() -> dict[str, str]:
    return {
        "nombre": "Usuario RBAC",
        "email": f"rbac.{uuid.uuid4()}@fiuner.edu.ar",
        "password": "Password#2026",
        "perfil": "docente",
    }


@given(parsers.parse('un JWT válido con rol "{rol}"'))
def jwt_valido_con_rol(context, rol):
    context["token"] = _token_valido(rol)


@given("un request a un recurso protegido sin header Authorization")
def sin_header_authorization(context):
    context["token"] = None


@given("un JWT cuyo exp ya pasó (más de 60 minutos desde la emisión, ADR-013)")
def jwt_expirado(context):
    context["token"] = _token_expirado("administrador")


def _headers(context) -> dict[str, str] | None:
    if context["token"] is None:
        return None
    return {"Authorization": f"Bearer {context['token']}"}


@when("se solicita un endpoint de administración de cuentas")
def solicita_endpoint_administracion(context):
    context["response"] = run_async(
        _post("/usuarios", _body_crear_usuario(), headers=_headers(context))
    )


@when("se solicita un endpoint de gestión del banco de preguntas")
def solicita_endpoint_banco_preguntas(context):
    # Banco de Preguntas todavía no existe como BC (Incremento 2) — el guard rol→recurso se
    # ejercita contra un endpoint real de Identidad protegido para `administrador`/`docente`,
    # que un Estudiante tampoco puede invocar (ver nota de implementación de la spec).
    context["response"] = run_async(
        _post("/usuarios", _body_crear_usuario(), headers=_headers(context))
    )


@when("se solicita un endpoint de analytics globales")
def solicita_endpoint_analytics(context):
    context["response"] = run_async(
        _post(
            f"/comisiones/{uuid.uuid4()}/invitaciones",
            {"docente_id": str(uuid.uuid4()), "email_destinatario": "x@fiuner.edu.ar"},
            headers=_headers(context),
        )
    )


@when("se solicita un endpoint de administración de cuentas (US-1.1.0)")
def solicita_endpoint_administracion_us110(context):
    context["response"] = run_async(
        _post("/usuarios", _body_crear_usuario(), headers=_headers(context))
    )


@when("se procesa el request")
def procesa_request(context):
    context["response"] = run_async(
        _post("/usuarios", _body_crear_usuario(), headers=_headers(context))
    )


@when("se solicita cualquier recurso protegido")
def solicita_recurso_protegido(context):
    context["response"] = run_async(
        _post("/usuarios", _body_crear_usuario(), headers=_headers(context))
    )


@then("el sistema concede el acceso y ejecuta el handler")
def valida_acceso_concedido(context):
    assert context["response"].status_code == 201


@then("el sistema responde 403 Forbidden")
def valida_403(context):
    assert context["response"].status_code == 403


@then("el sistema responde 401 Unauthorized")
def valida_401(context):
    assert context["response"].status_code == 401
