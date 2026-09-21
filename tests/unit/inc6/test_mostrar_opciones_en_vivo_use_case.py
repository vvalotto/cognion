"""Tests unitarios de `MostrarOpcionesEnVivoUseCase` y de su método en el controller (US-6.2.2)."""

from unittest.mock import AsyncMock
from uuid import uuid4

import pytest

from src.actividad_evaluativa.entities.errors import (
    ConcurrenciaOptimistaError,
    OpcionesYaMostradas,
    SesionNoEnCurso,
    SesionNoExiste,
)
from src.actividad_evaluativa.entities.ports.event_store_port import EventoParaAlmacenar
from src.actividad_evaluativa.entities.ports.pregunta_consulta_port import ContenidoPregunta
from src.actividad_evaluativa.interface_adapters.controllers.conduccion_en_vivo_controller import (
    ConduccionEnVivoController,
)
from src.actividad_evaluativa.use_cases.crear_sesion_en_vivo import CrearSesionEnVivoUseCase
from src.actividad_evaluativa.use_cases.iniciar_sesion_en_vivo import IniciarSesionEnVivoUseCase
from src.actividad_evaluativa.use_cases.mostrar_opciones_en_vivo import (
    AGGREGATE_TYPE_SESION,
    MostrarOpcionesEnVivoUseCase,
)
from tests.unit.inc3._fakes import (
    FakeEventStore,
    FakePreguntaConsultaPort,
)
from tests.unit.inc6._fakes import (
    FakeCanalTiempoReal,
    FakeComisionConsultaPort,
)

OPCIONES = ["A", "B", "C", "D"]


async def _escenario(opciones: list[str] | None = None, iniciada: bool = True):
    """Crea una sesión (y la inicia si se pide) y arma el use case de mostrar opciones."""
    comision_id, materia_id = uuid4(), uuid4()
    comision_consulta = FakeComisionConsultaPort()
    comision_consulta.materias[comision_id] = materia_id
    pregunta_consulta = FakePreguntaConsultaPort()
    ids = [uuid4() for _ in range(6)]
    pregunta_consulta.ids_activas[materia_id] = ids
    for i, pregunta_id in enumerate(ids):
        pregunta_consulta.contenidos[pregunta_id] = ContenidoPregunta(
            texto=f"Enunciado {i}", opciones=opciones
        )
    event_store = FakeEventStore()
    sesion = await CrearSesionEnVivoUseCase(
        comision_consulta, pregunta_consulta, event_store
    ).execute(comision_id, 3, 45)
    canal = FakeCanalTiempoReal()
    if iniciada:
        await IniciarSesionEnVivoUseCase(event_store, pregunta_consulta, canal).execute(sesion.id)
        canal.publicados.clear()
    use_case = MostrarOpcionesEnVivoUseCase(event_store, pregunta_consulta, canal)
    return use_case, event_store, canal, sesion, pregunta_consulta


class TestMostrarOpciones:
    async def test_persiste_el_evento_y_marca_las_opciones(self):
        use_case, event_store, _, sesion, _ = await _escenario(OPCIONES)

        resultado = await use_case.execute(sesion.id)

        assert resultado.opciones_mostradas is True
        assert resultado.opciones_mostradas_en is not None
        eventos = await event_store.load(AGGREGATE_TYPE_SESION, sesion.id)
        assert [e.event_type for e in eventos][-1] == "OpcionesEnVivoMostradas"
        assert eventos[-1].payload["opciones"] == OPCIONES
        assert eventos[-1].payload["ocurrido_en"] == resultado.opciones_mostradas_en.isoformat()

    async def test_publica_las_opciones_sin_la_correcta(self):
        use_case, _, canal, sesion, _ = await _escenario(OPCIONES)

        await use_case.execute(sesion.id)

        assert canal.publicados == [
            (
                sesion.id,
                {
                    "tipo": "opciones_mostradas",
                    "pregunta_actual_indice": 0,
                    "opciones": OPCIONES,
                    "tiempo_limite_por_pregunta_segundos": 45,
                    "cantidad_respuestas": 0,
                },
            )
        ]

    async def test_verdadero_falso_publica_opciones_nulas(self):
        use_case, _, canal, sesion, _ = await _escenario(None)

        await use_case.execute(sesion.id)

        assert canal.publicados[0][1]["opciones"] is None


class TestRechazos:
    async def test_sesion_inexistente(self):
        use_case, _, canal, _, _ = await _escenario()

        with pytest.raises(SesionNoExiste):
            await use_case.execute(uuid4())

        assert canal.publicados == []

    async def test_sesion_en_espera(self):
        use_case, event_store, canal, sesion, _ = await _escenario(OPCIONES, iniciada=False)

        with pytest.raises(SesionNoEnCurso):
            await use_case.execute(sesion.id)

        assert len(await event_store.load(AGGREGATE_TYPE_SESION, sesion.id)) == 1
        assert canal.publicados == []

    async def test_sesion_finalizada(self):
        use_case, event_store, canal, sesion, _ = await _escenario(OPCIONES)
        await event_store.append(
            AGGREGATE_TYPE_SESION,
            sesion.id,
            2,
            [
                EventoParaAlmacenar(
                    event_type="SesionEnVivoFinalizada", payload={"sesion_id": str(sesion.id)}
                )
            ],
        )

        with pytest.raises(SesionNoEnCurso):
            await use_case.execute(sesion.id)

        assert canal.publicados == []

    async def test_segunda_vez_se_rechaza_sin_persistir_ni_publicar(self):
        use_case, event_store, canal, sesion, _ = await _escenario(OPCIONES)
        await use_case.execute(sesion.id)

        with pytest.raises(OpcionesYaMostradas):
            await use_case.execute(sesion.id)

        assert len(await event_store.load(AGGREGATE_TYPE_SESION, sesion.id)) == 3
        assert len(canal.publicados) == 1

    async def test_carrera_de_dos_pedidos_deja_ganar_a_uno_solo(self):
        use_case, event_store, canal, sesion, _ = await _escenario(OPCIONES)
        original_append = event_store.append

        async def append_con_carrera(aggregate_type, aggregate_id, expected, events):
            await original_append(aggregate_type, aggregate_id, expected, events)
            raise ConcurrenciaOptimistaError(aggregate_type, aggregate_id, expected, expected + 1)

        event_store.append = append_con_carrera  # type: ignore[method-assign]

        with pytest.raises(OpcionesYaMostradas):
            await use_case.execute(sesion.id)

        assert canal.publicados == []


class TestSesionesEnVivoControllerMostrarOpciones:
    async def test_mostrar_opciones_delega_en_el_use_case(self):
        use_case, event_store, _, sesion, pregunta_consulta = await _escenario(OPCIONES)
        controller = ConduccionEnVivoController(use_case, AsyncMock(), AsyncMock(), AsyncMock())

        resultado = await controller.mostrar_opciones(sesion.id)

        assert resultado.opciones_mostradas is True
