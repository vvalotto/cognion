"""Steps BDD de US-ADJ-08 (`tests/features/inc6-adj/US-ADJ-08-invitacion-preview.feature`)."""

from __future__ import annotations

import asyncio
import uuid
from datetime import UTC, datetime, timedelta

import pytest
from httpx import ASGITransport, AsyncClient
from pytest_bdd import given, scenarios, then, when
from sqlalchemy import text

from src.app import app
from src.banco_preguntas.entities.materia import Materia
from src.banco_preguntas.interface_adapters.gateways.materia_repository import (
    SQLAlchemyMateriaRepository,
)
from src.identidad.entities.comision import Comision
from src.identidad.entities.invitacion import Invitacion
from src.identidad.entities.usuario import Usuario
from src.identidad.frameworks.db.models import InvitacionModel
from src.identidad.interface_adapters.gateways.comision_repository import (
    SQLAlchemyComisionRepository,
)
from src.identidad.interface_adapters.gateways.invitacion_repository import (
    SQLAlchemyInvitacionRepository,
)
from src.identidad.interface_adapters.gateways.usuario_repository import SQLAlchemyUsuarioRepository
from src.shared.entities.tipo_perfil import TipoPerfil
from src.shared.frameworks.db import SessionLocal

scenarios("../../features/inc6-adj/US-ADJ-08-invitacion-preview.feature")


def run_async(coro):
    """pytest-bdd no soporta step functions async def — ver ADR-018."""
    return asyncio.run(coro)


async def _limpiar_tablas() -> None:
    async with SessionLocal() as session:
        await session.execute(text("DELETE FROM invitacion"))
        await session.execute(text("DELETE FROM estudiante"))
        await session.execute(text("DELETE FROM comision_docentes"))
        await session.execute(text("DELETE FROM comision"))
        await session.execute(text("DELETE FROM docente"))
        await session.execute(text("DELETE FROM administrador"))
        await session.execute(text("DELETE FROM usuario"))
        await session.execute(text("DELETE FROM banco"))
        await session.execute(text("DELETE FROM materia"))
        await session.commit()


@pytest.fixture(autouse=True)
def limpiar_tablas():
    run_async(_limpiar_tablas())
    yield
    run_async(_limpiar_tablas())


@pytest.fixture
def context():
    return {}


async def _crear_invitacion_vigente() -> str:
    async with SessionLocal() as session:
        usuario_repo = SQLAlchemyUsuarioRepository(session)
        comision_repo = SQLAlchemyComisionRepository(session)
        invitacion_repo = SQLAlchemyInvitacionRepository(session)
        materia_repo = SQLAlchemyMateriaRepository(session)

        sufijo = uuid.uuid4()
        materia = Materia.crear(f"IS-2026-adj08-{sufijo}")
        await materia_repo.guardar(materia)
        admin = Usuario.crear("Vic", f"vic.{sufijo}@fiuner.edu.ar", "hash", TipoPerfil.ADMINISTRADOR)
        await usuario_repo.guardar(admin)
        docente = Usuario.crear("Ana", f"ana.{sufijo}@fiuner.edu.ar", "hash", TipoPerfil.DOCENTE)
        await usuario_repo.guardar(docente)
        comision = Comision.crear(materia.id, "lu 10-12", admin.id)
        await comision_repo.guardar(comision)

        invitacion = Invitacion.crear(comision.id, docente.id)
        await invitacion_repo.guardar(invitacion)
        return invitacion.token


async def _vencer_invitacion(token: str) -> None:
    async with SessionLocal() as session:
        invitacion_repo = SQLAlchemyInvitacionRepository(session)
        invitacion = await invitacion_repo.obtener_por_token(token)
        modelo = await session.get(InvitacionModel, invitacion.id)
        modelo.expira_en = datetime.now(UTC) - timedelta(days=1)
        await session.commit()


async def _marcar_usada(token: str) -> None:
    async with SessionLocal() as session:
        invitacion_repo = SQLAlchemyInvitacionRepository(session)
        invitacion = await invitacion_repo.obtener_por_token(token)
        modelo = await session.get(InvitacionModel, invitacion.id)
        modelo.usada_en = datetime.now(UTC)
        await session.commit()


async def _get(path: str):
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        return await client.get(path)


@given("una Invitación vigente para una Comisión de una Materia existente")
@given("una Invitación vigente")
def invitacion_vigente(context):
    context["token"] = run_async(_crear_invitacion_vigente())


@given("un token que no corresponde a ninguna Invitación")
def token_inexistente(context):
    context["token"] = "token-que-no-existe"


@given("una Invitación cuyo expira_en ya pasó")
def invitacion_vencida(context):
    token = run_async(_crear_invitacion_vigente())
    run_async(_vencer_invitacion(token))
    context["token"] = token


@given("una Invitación con usada_en distinto de null")
def invitacion_ya_usada(context):
    token = run_async(_crear_invitacion_vigente())
    run_async(_marcar_usada(token))
    context["token"] = token


@when("se consulta GET /identidad/invitaciones/{token} con ese token")
def consulta_invitacion(context):
    context["response"] = run_async(_get(f"/identidad/invitaciones/{context['token']}"))


@when("se consulta GET /identidad/invitaciones/{token} con ese token dos veces seguidas")
def consulta_invitacion_dos_veces(context):
    context["response"] = run_async(_get(f"/identidad/invitaciones/{context['token']}"))
    context["segunda_response"] = run_async(_get(f"/identidad/invitaciones/{context['token']}"))


@then("la respuesta tiene status code 200")
def valida_200(context):
    assert context["response"].status_code == 200


@then("la respuesta tiene status code 404")
def valida_404(context):
    assert context["response"].status_code == 404


@then("la respuesta tiene status code 422")
def valida_422(context):
    assert context["response"].status_code == 422


@then("la respuesta contiene el nombre de la Materia")
def valida_contiene_materia(context):
    assert context["response"].json()["materia"]


@then("la respuesta contiene el horario de la Comisión")
def valida_contiene_horario(context):
    assert context["response"].json()["horario"] == "lu 10-12"


@then("la respuesta no contiene el docente_id de la invitación")
def valida_sin_docente_id(context):
    assert "docente_id" not in context["response"].json()


@then("la respuesta no contiene ningún email destinatario")
def valida_sin_email(context):
    data = context["response"].json()
    assert "email_destinatario" not in data
    assert "email" not in data


@then("ambas respuestas tienen status code 200")
def valida_ambas_200(context):
    assert context["response"].status_code == 200
    assert context["segunda_response"].status_code == 200


@then("la Invitación sigue vigente (usada_en sigue en null)")
def valida_invitacion_sigue_vigente(context):
    async def _verificar():
        async with SessionLocal() as session:
            invitacion_repo = SQLAlchemyInvitacionRepository(session)
            invitacion = await invitacion_repo.obtener_por_token(context["token"])
            assert invitacion is not None
            assert invitacion.usada_en is None

    run_async(_verificar())
