"""Tests unitarios de `AvanzarSiguientePreguntaUseCase` y de su método en el controller (US-6.2.6)."""

from uuid import uuid4

import pytest

from src.actividad_evaluativa.entities.actividad_evaluativa_en_vivo import (
    ActividadEvaluativaEnVivo,
)
from src.actividad_evaluativa.entities.errors import (
    ConcurrenciaOptimistaError,
    NoQuedanPreguntas,
    PreguntaActualNoCerrada,
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
from src.actividad_evaluativa.use_cases.avanzar_siguiente_pregunta import (
    AGGREGATE_TYPE_SESION,
    AvanzarSiguientePreguntaUseCase,
)
from src.actividad_evaluativa.use_cases.cerrar_pregunta_actual import CerrarPreguntaActualUseCase
from src.actividad_evaluativa.use_cases.crear_sesion_en_vivo import CrearSesionEnVivoUseCase
from src.actividad_evaluativa.use_cases.iniciar_sesion_en_vivo import IniciarSesionEnVivoUseCase
from src.actividad_evaluativa.use_cases.mostrar_opciones_en_vivo import (
    MostrarOpcionesEnVivoUseCase,
)
from tests.unit.inc3._fakes import (
    FakeEstudianteConsultaPort,
    FakeEventStore,
    FakePreguntaConsultaPort,
)
from tests.unit.inc6._fakes import (
    FakeCanalTiempoReal,
    FakeComisionConsultaPort,
    FakeProyeccionesEnVivo,
)

OPCIONES = ["A", "B", "C", "D"]


async def _escenario(iniciada: bool = True, cerrada: bool = True, preguntas: int = 3):
    """Crea una sesión, la lleva al estado pedido y arma el use case de avanzar."""
    comision_id, materia_id = uuid4(), uuid4()
    comision_consulta = FakeComisionConsultaPort()
    comision_consulta.materias[comision_id] = materia_id
    pregunta_consulta = FakePreguntaConsultaPort()
    ids = [uuid4() for _ in range(preguntas)]
    pregunta_consulta.ids_activas[materia_id] = ids
    event_store = FakeEventStore()
    sesion = await CrearSesionEnVivoUseCase(
        comision_consulta, pregunta_consulta, event_store
    ).execute(comision_id, preguntas, 45)
    # `crear` baraja las preguntas: el contenido se asigna según el orden real de la sesión.
    for i, asignada in enumerate(sesion.preguntas):
        # La segunda es Verdadero/Falso: cubre la derivación del tipo.
        opciones = None if i == 1 else OPCIONES
        pregunta_consulta.contenidos[asignada.pregunta_id] = ContenidoPregunta(
            texto=f"Enunciado {i}", opciones=opciones
        )
        pregunta_consulta.detalles[asignada.pregunta_id] = DetalleCorreccionPregunta(
            texto=f"Detalle {i}", contenido_correcto={"opcion_indice": 2}, opciones=opciones
        )
    canal = FakeCanalTiempoReal()
    if iniciada:
        await IniciarSesionEnVivoUseCase(event_store, pregunta_consulta, canal).execute(sesion.id)
        await MostrarOpcionesEnVivoUseCase(event_store, pregunta_consulta, canal).execute(sesion.id)
    if iniciada and cerrada:
        await CerrarPreguntaActualUseCase(
            event_store, FakeProyeccionesEnVivo(), pregunta_consulta, canal, FakeEstudianteConsultaPort()
        ).execute(sesion.id)
    canal.publicados.clear()
    use_case = AvanzarSiguientePreguntaUseCase(event_store, pregunta_consulta, canal)
    return use_case, event_store, canal, sesion


class TestAvanzar:
    async def test_persiste_el_evento_y_deja_el_estado_inicial_de_la_pregunta(self):
        use_case, event_store, _, sesion = await _escenario()

        resultado = await use_case.execute(sesion.id)

        assert resultado.pregunta_actual_indice == 1
        assert resultado.opciones_mostradas is False
        assert resultado.pregunta_actual_cerrada is False
        eventos = await event_store.load(AGGREGATE_TYPE_SESION, sesion.id)
        assert eventos[-1].event_type == "SiguientePreguntaPresentada"
        assert eventos[-1].payload["pregunta_actual_indice"] == 1
        assert eventos[-1].payload["pregunta"] == {
            "pregunta_id": str(sesion.preguntas[1].pregunta_id),
            "enunciado": "Enunciado 1",
            "tipo": "verdadero_falso",
        }

    async def test_publica_el_mismo_mensaje_que_el_inicio_sin_opciones(self):
        use_case, _, canal, sesion = await _escenario()

        await use_case.execute(sesion.id)

        assert canal.publicados == [
            (
                sesion.id,
                {
                    "tipo": "pregunta_presentada",
                    "pregunta_actual_indice": 1,
                    "pregunta": {
                        "pregunta_id": str(sesion.preguntas[1].pregunta_id),
                        "enunciado": "Enunciado 1",
                        "tipo": "verdadero_falso",
                    },
                },
            )
        ]

    async def test_la_sesion_se_reconstruye_en_la_nueva_pregunta(self):
        use_case, event_store, _, sesion = await _escenario()
        await use_case.execute(sesion.id)

        eventos = await event_store.load(AGGREGATE_TYPE_SESION, sesion.id)
        reconstruida = ActividadEvaluativaEnVivo.reconstruir(eventos)

        assert reconstruida.pregunta_actual_indice == 1
        assert reconstruida.pregunta_actual_cerrada is False
        assert reconstruida.opciones_mostradas is False


class TestRechazos:
    async def test_sesion_inexistente(self):
        use_case, _, canal, _ = await _escenario()

        with pytest.raises(SesionNoExiste):
            await use_case.execute(uuid4())

        assert canal.publicados == []

    async def test_sesion_en_espera(self):
        use_case, event_store, canal, sesion = await _escenario(iniciada=False)

        with pytest.raises(SesionNoEnCurso):
            await use_case.execute(sesion.id)

        assert len(await event_store.load(AGGREGATE_TYPE_SESION, sesion.id)) == 1
        assert canal.publicados == []

    async def test_pregunta_sin_cerrar(self):
        use_case, event_store, canal, sesion = await _escenario(cerrada=False)

        with pytest.raises(PreguntaActualNoCerrada):
            await use_case.execute(sesion.id)

        assert len(await event_store.load(AGGREGATE_TYPE_SESION, sesion.id)) == 3
        assert canal.publicados == []

    async def test_ultima_pregunta(self):
        use_case, event_store, canal, sesion = await _escenario(preguntas=3)
        await use_case.execute(sesion.id)
        # Llevar la sesión a la última pregunta (índice 2 de 3), cerrada.
        await _cerrar_y_avanzar(use_case, event_store, canal, sesion.id)
        await _mostrar_y_cerrar(event_store, canal, sesion.id)
        cantidad = len(await event_store.load(AGGREGATE_TYPE_SESION, sesion.id))

        with pytest.raises(NoQuedanPreguntas):
            await use_case.execute(sesion.id)

        assert len(await event_store.load(AGGREGATE_TYPE_SESION, sesion.id)) == cantidad

    async def test_sesion_finalizada(self):
        use_case, event_store, canal, sesion = await _escenario()
        await event_store.append(
            AGGREGATE_TYPE_SESION,
            sesion.id,
            4,
            [
                EventoParaAlmacenar(
                    event_type="SesionEnVivoFinalizada", payload={"sesion_id": str(sesion.id)}
                )
            ],
        )

        with pytest.raises(SesionNoEnCurso):
            await use_case.execute(sesion.id)

        assert canal.publicados == []

    async def test_carrera_de_dos_avances_se_traduce_a_pregunta_no_cerrada(self):
        use_case, event_store, canal, sesion = await _escenario()
        original_append = event_store.append

        async def append_con_carrera(aggregate_type, aggregate_id, expected, events):
            await original_append(aggregate_type, aggregate_id, expected, events)
            raise ConcurrenciaOptimistaError(aggregate_type, aggregate_id, expected, expected + 1)

        event_store.append = append_con_carrera  # type: ignore[method-assign]

        with pytest.raises(PreguntaActualNoCerrada):
            await use_case.execute(sesion.id)

        assert canal.publicados == []


async def _mostrar_y_cerrar(event_store, canal, sesion_id):
    """Muestra las opciones y cierra la pregunta actual (para llegar a la última, cerrada)."""
    pregunta_consulta = FakePreguntaConsultaPort()
    eventos = await event_store.load(AGGREGATE_TYPE_SESION, sesion_id)
    sesion = ActividadEvaluativaEnVivo.reconstruir(eventos)
    pregunta_consulta.contenidos[sesion.pregunta_actual().pregunta_id] = ContenidoPregunta(
        texto="x", opciones=OPCIONES
    )
    pregunta_consulta.detalles[sesion.pregunta_actual().pregunta_id] = DetalleCorreccionPregunta(
        texto="x", contenido_correcto={"opcion_indice": 0}, opciones=OPCIONES
    )
    await MostrarOpcionesEnVivoUseCase(event_store, pregunta_consulta, canal).execute(sesion_id)
    await CerrarPreguntaActualUseCase(
        event_store, FakeProyeccionesEnVivo(), pregunta_consulta, canal, FakeEstudianteConsultaPort()
    ).execute(sesion_id)


async def _cerrar_y_avanzar(use_case, event_store, canal, sesion_id):
    """Cierra la pregunta actual (tras mostrar opciones) y avanza."""
    await _mostrar_y_cerrar(event_store, canal, sesion_id)
    await use_case.execute(sesion_id)


class TestConduccionEnVivoControllerAvanzar:
    async def test_avanzar_delega_en_el_use_case(self):
        use_case, _, _, sesion = await _escenario()
        controller = ConduccionEnVivoController(
            mostrar_opciones=None,  # type: ignore[arg-type]
            cerrar_pregunta=None,  # type: ignore[arg-type]
            avanzar_siguiente_pregunta=use_case,
            finalizar_sesion=None,  # type: ignore[arg-type]
        )

        resultado = await controller.avanzar_siguiente_pregunta(sesion.id)

        assert resultado.pregunta_actual_indice == 1
