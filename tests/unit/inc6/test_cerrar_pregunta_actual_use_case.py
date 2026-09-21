"""Tests unitarios de `CerrarPreguntaActualUseCase` y de su método en el controller (US-6.2.5)."""

from uuid import uuid4

import pytest

from src.actividad_evaluativa.entities.errors import (
    ConcurrenciaOptimistaError,
    OpcionesNoMostradasTodavia,
    PreguntaYaCerrada,
    SesionNoEnCurso,
    SesionNoExiste,
)
from src.actividad_evaluativa.entities.ports.event_store_port import EventoParaAlmacenar
from src.actividad_evaluativa.entities.ports.pregunta_consulta_port import (
    ContenidoPregunta,
    DetalleCorreccionPregunta,
)
from src.actividad_evaluativa.interface_adapters.controllers.conduccion_en_vivo_controller import (
    ConduccionEnVivoController,
)
from src.actividad_evaluativa.use_cases.cerrar_pregunta_actual import (
    AGGREGATE_TYPE_SESION,
    CerrarPreguntaActualUseCase,
)
from src.actividad_evaluativa.use_cases.crear_sesion_en_vivo import CrearSesionEnVivoUseCase
from src.actividad_evaluativa.use_cases.iniciar_sesion_en_vivo import IniciarSesionEnVivoUseCase
from src.actividad_evaluativa.use_cases.mostrar_opciones_en_vivo import (
    MostrarOpcionesEnVivoUseCase,
)
from tests.unit.inc3._fakes import FakeEventStore, FakePreguntaConsultaPort
from tests.unit.inc6._fakes import (
    FakeCanalTiempoReal,
    FakeComisionConsultaPort,
    FakeProyeccionesEnVivo,
)

OPCIONES = ["A", "B", "C", "D"]


async def _escenario(iniciada: bool = True, opciones_mostradas: bool = True):
    """Crea una sesión, la lleva al estado pedido y arma el use case de cerrar."""
    comision_id, materia_id = uuid4(), uuid4()
    comision_consulta = FakeComisionConsultaPort()
    comision_consulta.materias[comision_id] = materia_id
    pregunta_consulta = FakePreguntaConsultaPort()
    ids = [uuid4() for _ in range(6)]
    pregunta_consulta.ids_activas[materia_id] = ids
    for i, pregunta_id in enumerate(ids):
        pregunta_consulta.contenidos[pregunta_id] = ContenidoPregunta(
            texto=f"Enunciado {i}", opciones=OPCIONES
        )
        pregunta_consulta.detalles[pregunta_id] = DetalleCorreccionPregunta(
            texto=f"Detalle {pregunta_id}",
            contenido_correcto={"opcion_indice": 2},
            opciones=OPCIONES,
        )
    event_store = FakeEventStore()
    sesion = await CrearSesionEnVivoUseCase(
        comision_consulta, pregunta_consulta, event_store
    ).execute(comision_id, 3, 45)
    canal = FakeCanalTiempoReal()
    if iniciada:
        await IniciarSesionEnVivoUseCase(event_store, pregunta_consulta, canal).execute(sesion.id)
    if iniciada and opciones_mostradas:
        await MostrarOpcionesEnVivoUseCase(event_store, pregunta_consulta, canal).execute(sesion.id)
    canal.publicados.clear()
    proyecciones = FakeProyeccionesEnVivo()
    use_case = CerrarPreguntaActualUseCase(event_store, proyecciones, pregunta_consulta, canal)
    return use_case, event_store, canal, sesion, proyecciones


class TestCerrarPregunta:
    async def test_persiste_el_evento_y_marca_la_pregunta_cerrada(self):
        use_case, event_store, _, sesion, _ = await _escenario()

        resultado = await use_case.execute(sesion.id)

        assert resultado.pregunta_actual_cerrada is True
        eventos = await event_store.load(AGGREGATE_TYPE_SESION, sesion.id)
        assert eventos[-1].event_type == "PreguntaEnVivoCerrada"
        assert set(eventos[-1].payload) == {
            "sesion_id",
            "pregunta_actual_indice",
            "pregunta_id",
            "ocurrido_en",
        }

    async def test_publica_un_unico_mensaje_con_correcta_histograma_y_ranking(self):
        use_case, _, canal, sesion, proyecciones = await _escenario()
        a, b, c = uuid4(), uuid4(), uuid4()
        pregunta_id = sesion.preguntas[0].pregunta_id
        await proyecciones.registrar_respuesta(sesion.id, a, pregunta_id, "2", 900)
        await proyecciones.registrar_respuesta(sesion.id, b, pregunta_id, "0", 0)
        await proyecciones.registrar_respuesta(sesion.id, c, pregunta_id, "2", 1500)

        await use_case.execute(sesion.id)

        assert len(canal.publicados) == 1
        destino, mensaje = canal.publicados[0]
        assert destino == sesion.id
        assert mensaje["tipo"] == "pregunta_cerrada"
        assert mensaje["pregunta_actual_indice"] == 0
        assert mensaje["respuesta_correcta"] == {
            "contenido": {"opcion_indice": 2},
            "texto": f"Detalle {pregunta_id}",
            "opciones": OPCIONES,
        }
        assert mensaje["distribucion"] == [
            {"opcion": "0", "cantidad": 1},
            {"opcion": "2", "cantidad": 2},
        ]
        assert mensaje["ranking"] == [
            {"posicion": 1, "estudiante_id": str(c), "puntaje_acumulado": 1500},
            {"posicion": 2, "estudiante_id": str(a), "puntaje_acumulado": 900},
            {"posicion": 3, "estudiante_id": str(b), "puntaje_acumulado": 0},
        ]

    async def test_cierre_sin_respuestas_tiene_distribucion_vacia(self):
        use_case, _, canal, sesion, proyecciones = await _escenario()
        participante = uuid4()
        await proyecciones.inicializar_participante(sesion.id, participante)

        await use_case.execute(sesion.id)

        mensaje = canal.publicados[0][1]
        assert mensaje["distribucion"] == []
        assert mensaje["ranking"] == [
            {"posicion": 1, "estudiante_id": str(participante), "puntaje_acumulado": 0}
        ]


class TestRechazos:
    async def test_sesion_inexistente(self):
        use_case, _, canal, _, _ = await _escenario()

        with pytest.raises(SesionNoExiste):
            await use_case.execute(uuid4())

        assert canal.publicados == []

    async def test_sesion_en_espera(self):
        use_case, event_store, canal, sesion, _ = await _escenario(iniciada=False)

        with pytest.raises(SesionNoEnCurso):
            await use_case.execute(sesion.id)

        assert len(await event_store.load(AGGREGATE_TYPE_SESION, sesion.id)) == 1
        assert canal.publicados == []

    async def test_opciones_sin_mostrar(self):
        use_case, event_store, canal, sesion, _ = await _escenario(opciones_mostradas=False)

        with pytest.raises(OpcionesNoMostradasTodavia):
            await use_case.execute(sesion.id)

        assert len(await event_store.load(AGGREGATE_TYPE_SESION, sesion.id)) == 2
        assert canal.publicados == []

    async def test_segunda_vez_se_rechaza_sin_persistir_ni_publicar(self):
        use_case, event_store, canal, sesion, _ = await _escenario()
        await use_case.execute(sesion.id)

        with pytest.raises(PreguntaYaCerrada):
            await use_case.execute(sesion.id)

        assert len(await event_store.load(AGGREGATE_TYPE_SESION, sesion.id)) == 4
        assert len(canal.publicados) == 1

    async def test_carrera_de_dos_cierres_deja_ganar_a_uno_solo(self):
        use_case, event_store, canal, sesion, _ = await _escenario()
        original_append = event_store.append

        async def append_con_carrera(aggregate_type, aggregate_id, expected, events):
            await original_append(aggregate_type, aggregate_id, expected, events)
            raise ConcurrenciaOptimistaError(aggregate_type, aggregate_id, expected, expected + 1)

        event_store.append = append_con_carrera  # type: ignore[method-assign]

        with pytest.raises(PreguntaYaCerrada):
            await use_case.execute(sesion.id)

        assert canal.publicados == []

    async def test_sesion_finalizada(self):
        use_case, event_store, canal, sesion, _ = await _escenario()
        await event_store.append(
            AGGREGATE_TYPE_SESION,
            sesion.id,
            3,
            [
                EventoParaAlmacenar(
                    event_type="SesionEnVivoFinalizada", payload={"sesion_id": str(sesion.id)}
                )
            ],
        )

        with pytest.raises(SesionNoEnCurso):
            await use_case.execute(sesion.id)

        assert canal.publicados == []


class TestConduccionEnVivoControllerCerrar:
    async def test_cerrar_pregunta_delega_en_el_use_case(self):
        use_case, _, _, sesion, _ = await _escenario()
        controller = ConduccionEnVivoController(
            mostrar_opciones=None,  # type: ignore[arg-type]
            cerrar_pregunta=use_case,
            avanzar_siguiente_pregunta=None,  # type: ignore[arg-type]
            finalizar_sesion=None,  # type: ignore[arg-type]
        )

        resultado = await controller.cerrar_pregunta(sesion.id)

        assert resultado.pregunta_actual_cerrada is True
