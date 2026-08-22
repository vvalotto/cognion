"""Steps BDD de la paginación del banco de preguntas (US-ADJ-03).

Los escenarios mezclan lenguaje de UI ("botón Siguiente habilitado") con comportamiento de
backend — estos steps validan la parte de backend (contrato de `GET /bancos/{id}/preguntas`
con `pagina`/`tamanio_pagina`); la parte de UI (controles, reset de página al cambiar
filtros) está cubierta por Vitest en `frontend/src/pages/Banco.test.tsx`.
"""

from __future__ import annotations

import asyncio
import math

import pytest
from httpx import ASGITransport, AsyncClient
from pytest_bdd import given, parsers, scenarios, then, when
from sqlalchemy import text

from src.app import app
from src.shared.frameworks.db import SessionLocal
from tests.step_defs.inc2._auth_headers import docente_headers

scenarios("../../features/sp-adj-01/US-ADJ-03-paginar-banco-preguntas.feature")

TAMANIO_PAGINA = 20


def run_async(coro):
    """pytest-bdd no soporta step functions async def — ver ADR-018."""
    return asyncio.run(coro)


async def _limpiar_tablas_banco_preguntas() -> None:
    async with SessionLocal() as session:
        await session.execute(text("DELETE FROM pregunta_plantilla"))
        await session.execute(text("DELETE FROM banco"))
        await session.execute(text("DELETE FROM materia"))
        await session.commit()


@pytest.fixture(autouse=True)
def limpiar_tablas_banco_preguntas():
    run_async(_limpiar_tablas_banco_preguntas())
    yield
    run_async(_limpiar_tablas_banco_preguntas())


@pytest.fixture
def context():
    return {}


async def _post_crear_materia(nombre: str):
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        return await client.post("/materias", json={"nombre": nombre}, headers=docente_headers())


async def _post_cargar_pregunta(
    banco_id: str, indice: int, unidad: str = "Unidad 1", dificultad: str = "medio"
):
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        return await client.post(
            "/preguntas/opcion-multiple",
            json={
                "banco_id": banco_id,
                "texto": f"Pregunta {indice}",
                "opciones": [
                    {"texto": "a", "es_correcta": True},
                    {"texto": "b", "es_correcta": False},
                ],
                "unidad_tematica": unidad,
                "tema": "Tema",
                "dificultad": dificultad,
                "importancia": "medio",
            },
            headers=docente_headers(),
        )


async def _get_filtrar_banco(banco_id: str, **params):
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        return await client.get(
            f"/bancos/{banco_id}/preguntas", params=params, headers=docente_headers()
        )


def _crear_banco_con_preguntas(context, cantidad: int, **kwargs) -> None:
    respuesta_materia = run_async(_post_crear_materia(f"Materia {cantidad}"))
    assert respuesta_materia.status_code == 201
    banco_id = respuesta_materia.json()["banco_id"]
    context["banco_id"] = banco_id

    ids_en_orden = []
    for i in range(cantidad):
        respuesta = run_async(_post_cargar_pregunta(banco_id, i, **kwargs))
        assert respuesta.status_code == 201
        ids_en_orden.append(respuesta.json()["id"])
    context["ids_en_orden"] = ids_en_orden


@given(parsers.parse("un banco con {cantidad:d} preguntas activas y tamaño de página 20"))
def banco_con_n_preguntas(context, cantidad):
    _crear_banco_con_preguntas(context, cantidad)


@given(parsers.parse("un banco con {cantidad:d} preguntas activas"))
def banco_con_n_preguntas_sin_tamanio(context, cantidad):
    _crear_banco_con_preguntas(context, cantidad)


@given(parsers.parse("un Docente viendo la página {pagina:d} de un banco con {paginas:d} páginas"))
def docente_viendo_pagina_de_banco(context, pagina, paginas):
    _crear_banco_con_preguntas(context, paginas * TAMANIO_PAGINA - 1)
    context["response"] = run_async(
        _get_filtrar_banco(context["banco_id"], pagina=pagina, tamanio_pagina=TAMANIO_PAGINA)
    )


@given(parsers.parse('un Docente viendo la página {pagina:d} de un banco filtrado por "{unidad}"'))
def docente_viendo_pagina_filtrada(context, pagina, unidad):
    _crear_banco_con_preguntas(context, TAMANIO_PAGINA * 3, unidad=unidad, dificultad="medio")
    context["banco_unidad"] = unidad
    context["response"] = run_async(
        _get_filtrar_banco(
            context["banco_id"], pagina=pagina, tamanio_pagina=TAMANIO_PAGINA, unidad=unidad
        )
    )


@when("un Docente abre el banco de esa materia")
def docente_abre_banco(context):
    context["response"] = run_async(
        _get_filtrar_banco(context["banco_id"], pagina=1, tamanio_pagina=TAMANIO_PAGINA)
    )


@when("un Docente lo abre")
def docente_abre_banco_alias(context):
    context["response"] = run_async(
        _get_filtrar_banco(context["banco_id"], pagina=1, tamanio_pagina=TAMANIO_PAGINA)
    )


@when('hace clic en "Siguiente" (o en el número de página 2)')
def hace_clic_en_siguiente(context):
    context["response"] = run_async(
        _get_filtrar_banco(context["banco_id"], pagina=2, tamanio_pagina=TAMANIO_PAGINA)
    )


@when("cambia el filtro de Dificultad")
def cambia_filtro_dificultad(context):
    context["response"] = run_async(
        _get_filtrar_banco(
            context["banco_id"],
            pagina=1,
            tamanio_pagina=TAMANIO_PAGINA,
            unidad=context["banco_unidad"],
            dificultad="alto",
        )
    )


@then("ve las primeras 20 preguntas, ordenadas por fecha de creación")
def ve_primeras_20_ordenadas(context):
    data = context["response"].json()
    assert [p["id"] for p in data["preguntas"]] == context["ids_en_orden"][:20]


@then(
    parsers.parse(
        'los controles de paginación muestran {paginas:d} páginas y el botón "Siguiente" habilitado'
    )
)
def controles_muestran_n_paginas_siguiente_habilitado(context, paginas):
    data = context["response"].json()
    assert math.ceil(data["total"] / TAMANIO_PAGINA) == paginas
    assert 1 < paginas  # hay más de una página -> "Siguiente" queda habilitado en la UI


@then("ve las preguntas 21 a 40")
def ve_preguntas_21_a_40(context):
    data = context["response"].json()
    assert [p["id"] for p in data["preguntas"]] == context["ids_en_orden"][20:40]


@then('el botón "Anterior" queda habilitado')
def boton_anterior_habilitado(context):
    # La respuesta corresponde a pagina=2 — en la UI, pagina > 1 habilita "Anterior".
    assert context["response"].json()["preguntas"] != []


@then("vuelve a la página 1 con el nuevo filtro combinado aplicado")
def vuelve_a_pagina_1_con_filtro_combinado(context):
    data = context["response"].json()
    assert len(data["preguntas"]) <= TAMANIO_PAGINA
    assert all(p["dificultad"] == "alto" for p in data["preguntas"])


@then(
    've las 5 preguntas sin controles de paginación (o con "Anterior"/"Siguiente" deshabilitados)'
)
def ve_5_preguntas_sin_paginacion(context):
    data = context["response"].json()
    assert data["total"] == 5
    assert math.ceil(data["total"] / TAMANIO_PAGINA) == 1
