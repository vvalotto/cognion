"""Steps BDD de US-4.2.3 (`tests/features/inc4/US-4.2.3-pregunta-metadato-query-port.feature`)."""

from __future__ import annotations

import asyncio
import uuid

import pytest
from pytest_bdd import given, scenarios, then, when
from sqlalchemy import text

from src.analytics.frameworks.adapters.pregunta_metadato_consulta_port_in_process import (
    PreguntaMetadatoConsultaPortInProcess,
)
from src.banco_preguntas.entities.banco import Banco
from src.banco_preguntas.entities.dificultad import Dificultad
from src.banco_preguntas.entities.importancia import Importancia
from src.banco_preguntas.entities.materia import Materia
from src.banco_preguntas.entities.metadatos_pregunta import MetadatosPregunta
from src.banco_preguntas.entities.opcion import Opcion
from src.banco_preguntas.entities.pregunta_plantilla import PreguntaPlantillaOpcionMultiple
from src.banco_preguntas.interface_adapters.gateways.banco_repository import (
    SQLAlchemyBancoRepository,
)
from src.banco_preguntas.interface_adapters.gateways.materia_repository import (
    SQLAlchemyMateriaRepository,
)
from src.banco_preguntas.interface_adapters.gateways.pregunta_repository import (
    SQLAlchemyPreguntaRepository,
)
from src.shared.frameworks.db import SessionLocal

scenarios("../../features/inc4/US-4.2.3-pregunta-metadato-query-port.feature")


def run_async(coro):
    """pytest-bdd no soporta step functions async def — ver ADR-018."""
    return asyncio.run(coro)


async def _limpiar_tablas() -> None:
    async with SessionLocal() as session:
        await session.execute(text("DELETE FROM pregunta_plantilla"))
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


async def _banco_persistido(session) -> Banco:
    materia_repo = SQLAlchemyMateriaRepository(session)
    banco_repo = SQLAlchemyBancoRepository(session)
    materia = Materia.crear(f"Ingeniería de Software {uuid.uuid4()}")
    await materia_repo.guardar(materia)
    banco = Banco.crear(materia.id)
    await banco_repo.guardar(banco)
    return banco


async def _pregunta_persistida(
    session, banco_id, unidad_tematica: str, tema: str
) -> PreguntaPlantillaOpcionMultiple:
    pregunta_repo = SQLAlchemyPreguntaRepository(session)
    pregunta = PreguntaPlantillaOpcionMultiple.crear(
        banco_id=banco_id,
        metadatos=MetadatosPregunta(
            texto=f"Pregunta {uuid.uuid4()}",
            unidad_tematica=unidad_tematica,
            tema=tema,
            dificultad=Dificultad.MEDIO,
            importancia=Importancia.ALTO,
        ),
        opciones=[Opcion(texto="A", es_correcta=True), Opcion(texto="B", es_correcta=False)],
    )
    await pregunta_repo.guardar(pregunta)
    return pregunta


@given("3 preguntas con unidad_tematica/tema distintos")
def tres_preguntas_con_metadatos_distintos(context):
    async def _setup():
        async with SessionLocal() as session:
            banco = await _banco_persistido(session)
            p1 = await _pregunta_persistida(session, banco.id, "Unidad 1", "Herencia")
            p2 = await _pregunta_persistida(session, banco.id, "Unidad 1", "Polimorfismo")
            p3 = await _pregunta_persistida(session, banco.id, "Unidad 2", "Acoplamiento")
            context["ids"] = [p1.id, p2.id, p3.id]
            context["esperado"] = {
                p1.id: ("Unidad 1", "Herencia"),
                p2.id: ("Unidad 1", "Polimorfismo"),
                p3.id: ("Unidad 2", "Acoplamiento"),
            }

    run_async(_setup())


@given("2 preguntas existentes y 1 id que no corresponde a ninguna")
def dos_preguntas_y_un_id_inexistente(context):
    async def _setup():
        async with SessionLocal() as session:
            banco = await _banco_persistido(session)
            p1 = await _pregunta_persistida(session, banco.id, "Unidad 1", "Herencia")
            p2 = await _pregunta_persistida(session, banco.id, "Unidad 1", "Polimorfismo")
            context["id_inexistente"] = uuid.uuid4()
            context["ids"] = [p1.id, p2.id, context["id_inexistente"]]

    run_async(_setup())


@given("una pregunta con activa=false y sus metadatos de unidad_tematica/tema")
def pregunta_eliminada_con_metadatos(context):
    async def _setup():
        async with SessionLocal() as session:
            banco = await _banco_persistido(session)
            pregunta = await _pregunta_persistida(session, banco.id, "Unidad 3", "Cohesión")
            pregunta_repo = SQLAlchemyPreguntaRepository(session)
            pregunta.eliminar()
            await pregunta_repo.actualizar(pregunta)
            context["pregunta_id"] = pregunta.id
            context["esperado_tema"] = "Cohesión"

    run_async(_setup())


@when("PreguntaMetadatoConsultaPort.obtener_metadatos([id1, id2, id3]) se invoca")
def invoca_obtener_metadatos_con_ids_del_contexto(context):
    async def _call():
        async with SessionLocal() as session:
            adapter = PreguntaMetadatoConsultaPortInProcess(session)
            return await adapter.obtener_metadatos(context["ids"])

    context["resultado"] = run_async(_call())


@when("se invoca obtener_metadatos con los 3 ids")
def invoca_obtener_metadatos_con_los_3_ids(context):
    async def _call():
        async with SessionLocal() as session:
            adapter = PreguntaMetadatoConsultaPortInProcess(session)
            return await adapter.obtener_metadatos(context["ids"])

    context["resultado"] = run_async(_call())


@when("se invoca obtener_metadatos([])")
def invoca_obtener_metadatos_vacio(context):
    async def _call():
        async with SessionLocal() as session:
            adapter = PreguntaMetadatoConsultaPortInProcess(session)
            return await adapter.obtener_metadatos([])

    context["resultado"] = run_async(_call())


@when("se invoca obtener_metadatos incluyendo su id")
def invoca_obtener_metadatos_incluyendo_su_id(context):
    async def _call():
        async with SessionLocal() as session:
            adapter = PreguntaMetadatoConsultaPortInProcess(session)
            return await adapter.obtener_metadatos([context["pregunta_id"]])

    context["resultado"] = run_async(_call())


@then("devuelve un dict con las 3 entradas, cada una con su unidad_tematica/tema correcto")
def valida_dict_con_3_entradas_correctas(context):
    resultado = context["resultado"]
    assert len(resultado) == 3
    for pregunta_id, (unidad, tema) in context["esperado"].items():
        assert resultado[pregunta_id].unidad_tematica == unidad
        assert resultado[pregunta_id].tema == tema


@then("el dict resultado tiene 2 entradas, sin lanzar error por el id faltante")
def valida_dict_con_2_entradas_sin_error(context):
    resultado = context["resultado"]
    assert len(resultado) == 2
    assert context["id_inexistente"] not in resultado


@then("devuelve un dict vacío")
def valida_dict_vacio(context):
    assert context["resultado"] == {}


@then("el dict resultado incluye esa entrada — el metadato no depende del estado activa")
def valida_pregunta_eliminada_incluida(context):
    resultado = context["resultado"]
    assert context["pregunta_id"] in resultado
    assert resultado[context["pregunta_id"]].tema == context["esperado_tema"]
