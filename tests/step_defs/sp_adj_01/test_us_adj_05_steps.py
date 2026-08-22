"""Steps BDD de la paginación del listado de cuentas (US-ADJ-05).

Los escenarios mezclan lenguaje de UI ("botón Siguiente habilitado") con comportamiento de
backend — estos steps validan la parte de backend (contrato de `GET /usuarios` con
`pagina`/`tamanio_pagina`); la parte de UI (controles, reset de página al cambiar filtros)
está cubierta por Vitest en `frontend/src/pages/Cuentas.test.tsx`.
"""

from __future__ import annotations

import asyncio
import math
import uuid

import pytest
from httpx import ASGITransport, AsyncClient
from pytest_bdd import given, parsers, scenarios, then, when
from sqlalchemy import text

from src.app import app
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
from tests.step_defs.inc1._auth_headers import admin_headers

scenarios("../../features/sp-adj-01/US-ADJ-05-paginar-cuentas.feature")

TAMANIO_PAGINA = 20


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


async def _crear_cuenta_docente(indice: int) -> str:
    hasher = BcryptPasswordHasher()
    async with SessionLocal() as session:
        usuario_repo = SQLAlchemyUsuarioRepository(session)
        usuario = Usuario.crear(
            f"Docente {indice}",
            f"docente{indice}.{uuid.uuid4()}@fiuner.edu.ar",
            hasher.hash("Correcta#2026"),
            TipoPerfil.DOCENTE,
        )
        await usuario_repo.guardar(usuario)
        return str(usuario.id)


async def _crear_cuenta_estudiante_bloqueada(indice: int, comision_id: uuid.UUID) -> str:
    hasher = BcryptPasswordHasher()
    async with SessionLocal() as session:
        usuario_repo = SQLAlchemyUsuarioRepository(session)
        usuario = Usuario.crear_estudiante(
            f"Estudiante Bloqueado {indice}",
            f"estudiante{indice}.{uuid.uuid4()}@fiuner.edu.ar",
            hasher.hash("Correcta#2026"),
            comision_id,
        )
        usuario.bloqueada = True
        await usuario_repo.guardar(usuario)
        return str(usuario.id)


async def _crear_comision_dummy() -> uuid.UUID:
    hasher = BcryptPasswordHasher()
    async with SessionLocal() as session:
        usuario_repo = SQLAlchemyUsuarioRepository(session)
        comision_repo = SQLAlchemyComisionRepository(session)
        admin = Usuario.crear(
            "Admin BDD Comision",
            f"admin.bddadj05.{uuid.uuid4()}@fiuner.edu.ar",
            hasher.hash("x"),
            TipoPerfil.ADMINISTRADOR,
        )
        await usuario_repo.guardar(admin)
        comision = Comision.crear(uuid.uuid4(), "lu 10-12", admin.id)
        await comision_repo.guardar(comision)
        return comision.id


async def _get(path: str, params: dict) -> object:
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        return await client.get(path, params=params, headers=admin_headers())


def _crear_n_docentes(context, cantidad: int) -> None:
    ids_en_orden = [run_async(_crear_cuenta_docente(i)) for i in range(cantidad)]
    context["ids_en_orden"] = ids_en_orden


@given(parsers.parse("más de {cantidad:d} cuentas registradas que matchean los filtros activos"))
def mas_de_n_cuentas(context, cantidad):
    _crear_n_docentes(context, cantidad + 1)


@given("un Administrador viendo la página 1 de un listado con más de una página")
def admin_viendo_pagina_1_con_mas_de_una_pagina(context):
    _crear_n_docentes(context, TAMANIO_PAGINA + 1)
    context["response"] = run_async(
        _get("/usuarios", {"pagina": 1, "tamanio_pagina": TAMANIO_PAGINA})
    )


@given('un Administrador viendo la página 2 filtrado por rol "Estudiante"')
def admin_viendo_pagina_2_filtrado_por_rol(context):
    comision_id = run_async(_crear_comision_dummy())
    for i in range(TAMANIO_PAGINA * 3):
        run_async(_crear_cuenta_estudiante_bloqueada(i, comision_id))
    context["response"] = run_async(
        _get(
            "/usuarios",
            {"pagina": 2, "tamanio_pagina": TAMANIO_PAGINA, "rol": "estudiante"},
        )
    )


@given(parsers.parse("menos de {cantidad:d} cuentas que matchean los filtros"))
def menos_de_n_cuentas(context, cantidad):
    _crear_n_docentes(context, cantidad - 15)


@when("un Administrador abre el listado de cuentas")
def admin_abre_listado(context):
    context["response"] = run_async(
        _get("/usuarios", {"pagina": 1, "tamanio_pagina": TAMANIO_PAGINA})
    )


@when('hace clic en "Siguiente" (o en el número de página 2)')
def hace_clic_en_siguiente(context):
    context["response"] = run_async(
        _get("/usuarios", {"pagina": 2, "tamanio_pagina": TAMANIO_PAGINA})
    )


@when("cambia el filtro de Estado")
def cambia_filtro_estado(context):
    context["response"] = run_async(
        _get(
            "/usuarios",
            {"pagina": 1, "tamanio_pagina": TAMANIO_PAGINA, "rol": "estudiante", "estado": "bloqueada"},
        )
    )


@when("un Administrador lo abre")
def admin_abre_listado_alias(context):
    context["response"] = run_async(
        _get("/usuarios", {"pagina": 1, "tamanio_pagina": TAMANIO_PAGINA})
    )


@then("ve las primeras 20 cuentas, ordenadas por fecha de creación")
def ve_primeras_20_ordenadas(context):
    data = context["response"].json()
    ids_pagina = [c["id"] for c in data["cuentas"]]
    assert ids_pagina == context["ids_en_orden"][:20]


@then("los controles de paginación muestran la cantidad de páginas correspondiente")
def controles_muestran_cantidad_de_paginas(context):
    data = context["response"].json()
    assert math.ceil(data["total"] / TAMANIO_PAGINA) >= 2


@then("ve las cuentas 21 a 40")
def ve_cuentas_21_a_40(context):
    data = context["response"].json()
    ids_pagina = [c["id"] for c in data["cuentas"]]
    assert ids_pagina == context["ids_en_orden"][20:40]


@then('el botón "Anterior" queda habilitado')
def boton_anterior_habilitado(context):
    assert context["response"].json()["cuentas"] != []


@then("vuelve a la página 1 con el nuevo filtro combinado aplicado")
def vuelve_a_pagina_1_con_filtro_combinado(context):
    data = context["response"].json()
    assert len(data["cuentas"]) <= TAMANIO_PAGINA
    assert all(c["perfil"] == "estudiante" and c["bloqueada"] for c in data["cuentas"])


@then(
    've todas las cuentas sin controles de paginación (o con "Anterior"/"Siguiente" deshabilitados)'
)
def ve_todas_sin_controles_de_paginacion(context):
    data = context["response"].json()
    assert math.ceil(data["total"] / TAMANIO_PAGINA) == 1
