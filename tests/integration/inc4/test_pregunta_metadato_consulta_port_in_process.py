"""Test de integración del adapter in-process de Analytics hacia Banco de Preguntas (US-4.2.3).

Cubre los escenarios de `tests/features/inc4/US-4.2.3-pregunta-metadato-query-port.feature`
contra una base de datos real.
"""

import uuid

import pytest
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


async def _limpiar_tablas_banco_preguntas(session) -> None:
    """`tests/integration/inc4/conftest.py` no limpia estas tablas (solo `events`) — mismo
    criterio que `tests/step_defs/inc4/test_us_4_2_2_steps.py` (limpieza local por archivo)."""
    await session.execute(text("DELETE FROM pregunta_plantilla"))
    await session.execute(text("DELETE FROM banco"))
    await session.execute(text("DELETE FROM materia"))
    await session.commit()


@pytest.fixture(autouse=True)
async def limpiar_tablas_banco_preguntas(session):
    await _limpiar_tablas_banco_preguntas(session)
    yield
    await _limpiar_tablas_banco_preguntas(session)


async def _banco_persistido(session) -> Banco:
    materia_repo = SQLAlchemyMateriaRepository(session)
    banco_repo = SQLAlchemyBancoRepository(session)
    materia = Materia.crear(f"Ingeniería de Software {uuid.uuid4()}")
    await materia_repo.guardar(materia)
    banco = Banco.crear(materia.id)
    await banco_repo.guardar(banco)
    return banco


async def _pregunta_persistida(
    session, banco_id: uuid.UUID, unidad_tematica: str, tema: str
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


class TestPreguntaMetadatoConsultaPortInProcess:
    async def test_lote_de_preguntas_existentes(self, session):
        banco = await _banco_persistido(session)
        p1 = await _pregunta_persistida(session, banco.id, "Unidad 1", "Herencia")
        p2 = await _pregunta_persistida(session, banco.id, "Unidad 1", "Polimorfismo")
        p3 = await _pregunta_persistida(session, banco.id, "Unidad 2", "Acoplamiento")

        adapter = PreguntaMetadatoConsultaPortInProcess(session)
        resultado = await adapter.obtener_metadatos([p1.id, p2.id, p3.id])

        assert len(resultado) == 3
        assert resultado[p1.id].unidad_tematica == "Unidad 1"
        assert resultado[p1.id].tema == "Herencia"
        assert resultado[p2.id].tema == "Polimorfismo"
        assert resultado[p3.id].unidad_tematica == "Unidad 2"

    async def test_lote_con_un_id_inexistente(self, session):
        banco = await _banco_persistido(session)
        p1 = await _pregunta_persistida(session, banco.id, "Unidad 1", "Herencia")
        p2 = await _pregunta_persistida(session, banco.id, "Unidad 1", "Polimorfismo")
        id_inexistente = uuid.uuid4()

        adapter = PreguntaMetadatoConsultaPortInProcess(session)
        resultado = await adapter.obtener_metadatos([p1.id, p2.id, id_inexistente])

        assert len(resultado) == 2
        assert id_inexistente not in resultado

    async def test_lote_vacio_devuelve_dict_vacio(self, session):
        adapter = PreguntaMetadatoConsultaPortInProcess(session)

        resultado = await adapter.obtener_metadatos([])

        assert resultado == {}

    async def test_pregunta_eliminada_igual_aparece_en_el_resultado(self, session):
        banco = await _banco_persistido(session)
        pregunta = await _pregunta_persistida(session, banco.id, "Unidad 3", "Cohesión")
        pregunta_repo = SQLAlchemyPreguntaRepository(session)
        pregunta.eliminar()
        await pregunta_repo.actualizar(pregunta)

        adapter = PreguntaMetadatoConsultaPortInProcess(session)
        resultado = await adapter.obtener_metadatos([pregunta.id])

        assert pregunta.id in resultado
        assert resultado[pregunta.id].tema == "Cohesión"
