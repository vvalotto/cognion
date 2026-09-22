"""Tests unitarios de `FinalizarSesionEnVivoUseCase`, `finalizar()` y el controller (US-6.2.7)."""

from uuid import uuid4

import pytest

from src.actividad_evaluativa.entities.actividad_evaluativa_en_vivo import (
    ActividadEvaluativaEnVivo,
    EstadoSesionEnVivo,
)
from src.actividad_evaluativa.entities.errors import (
    ConcurrenciaOptimistaError,
    PreguntaActualNoCerrada,
    SesionNoEnCurso,
    SesionNoExiste,
    SesionYaFinalizada,
)
from src.actividad_evaluativa.entities.ports.pregunta_consulta_port import (
    ContenidoPregunta,
    DetalleCorreccionPregunta,
)
from src.actividad_evaluativa.interface_adapters.controllers.conduccion_en_vivo_controller import (
    ConduccionEnVivoController,
)
from src.actividad_evaluativa.use_cases.cerrar_pregunta_actual import CerrarPreguntaActualUseCase
from src.actividad_evaluativa.use_cases.crear_sesion_en_vivo import CrearSesionEnVivoUseCase
from src.actividad_evaluativa.use_cases.finalizar_sesion_en_vivo import (
    AGGREGATE_TYPE_SESION,
    FinalizarSesionEnVivoUseCase,
)
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
    """Crea una sesión, la lleva al estado pedido y arma el use case de finalizar."""
    comision_id, materia_id = uuid4(), uuid4()
    comision_consulta = FakeComisionConsultaPort()
    comision_consulta.materias[comision_id] = materia_id
    pregunta_consulta = FakePreguntaConsultaPort()
    pregunta_consulta.ids_activas[materia_id] = [uuid4() for _ in range(preguntas)]
    event_store = FakeEventStore()
    sesion = await CrearSesionEnVivoUseCase(
        comision_consulta, pregunta_consulta, event_store
    ).execute(comision_id, preguntas, 45)
    for i, asignada in enumerate(sesion.preguntas):
        pregunta_consulta.contenidos[asignada.pregunta_id] = ContenidoPregunta(
            texto=f"Enunciado {i}", opciones=OPCIONES
        )
        pregunta_consulta.detalles[asignada.pregunta_id] = DetalleCorreccionPregunta(
            texto=f"Detalle {i}", contenido_correcto={"opcion_indice": 2}, opciones=OPCIONES
        )
    proyecciones = FakeProyeccionesEnVivo()
    canal = FakeCanalTiempoReal()
    if iniciada:
        await IniciarSesionEnVivoUseCase(event_store, pregunta_consulta, canal).execute(sesion.id)
        await MostrarOpcionesEnVivoUseCase(event_store, pregunta_consulta, canal).execute(sesion.id)
    estudiante_consulta = FakeEstudianteConsultaPort()
    if iniciada and cerrada:
        await CerrarPreguntaActualUseCase(
            event_store, proyecciones, pregunta_consulta, canal, estudiante_consulta
        ).execute(sesion.id)
    canal.publicados.clear()
    use_case = FinalizarSesionEnVivoUseCase(
        event_store, proyecciones, canal, estudiante_consulta
    )
    return use_case, event_store, canal, sesion, proyecciones, estudiante_consulta


class TestFinalizar:
    async def test_persiste_el_evento_y_pasa_a_finalizada(self):
        use_case, event_store, _, sesion, _, _ = await _escenario()

        resultado = await use_case.execute(sesion.id)

        assert resultado.estado == EstadoSesionEnVivo.FINALIZADA
        eventos = await event_store.load(AGGREGATE_TYPE_SESION, sesion.id)
        assert eventos[-1].event_type == "SesionEnVivoFinalizada"
        assert eventos[-1].payload["sesion_id"] == str(sesion.id)
        assert "ranking" not in eventos[-1].payload

    async def test_finalizacion_anticipada_con_preguntas_sin_presentar(self):
        use_case, _, _, sesion, _, _ = await _escenario(preguntas=5)

        resultado = await use_case.execute(sesion.id)

        assert resultado.pregunta_actual_indice == 0
        assert resultado.estado == EstadoSesionEnVivo.FINALIZADA

    async def test_publica_el_ranking_final_ordenado_por_puntaje(self):
        use_case, _, canal, sesion, proyecciones, _ = await _escenario()
        ana, beto = uuid4(), uuid4()
        await proyecciones.registrar_respuesta(sesion.id, ana, uuid4(), "A", 300)
        await proyecciones.registrar_respuesta(sesion.id, beto, uuid4(), "A", 900)

        await use_case.execute(sesion.id)

        assert canal.publicados == [
            (
                sesion.id,
                {
                    "tipo": "sesion_finalizada",
                    "ranking": [
                        {
                            "posicion": 1,
                            "estudiante_id": str(beto),
                            "puntaje_acumulado": 900,
                            "nombre": "Estudiante sin nombre",
                        },
                        {
                            "posicion": 2,
                            "estudiante_id": str(ana),
                            "puntaje_acumulado": 300,
                            "nombre": "Estudiante sin nombre",
                        },
                    ],
                },
            )
        ]

    async def test_ranking_final_trae_el_nombre_resuelto_de_cada_estudiante(self):
        use_case, _, canal, sesion, proyecciones, estudiante_consulta = await _escenario()
        ana = uuid4()
        await proyecciones.registrar_respuesta(sesion.id, ana, uuid4(), "A", 300)
        estudiante_consulta.nombres_por_estudiante[ana] = "Ana Torres"

        await use_case.execute(sesion.id)

        mensaje = canal.publicados[0][1]
        assert mensaje["ranking"][0]["nombre"] == "Ana Torres"

    async def test_la_sesion_se_reconstruye_finalizada(self):
        use_case, event_store, _, sesion, _, _ = await _escenario()
        await use_case.execute(sesion.id)

        eventos = await event_store.load(AGGREGATE_TYPE_SESION, sesion.id)

        assert ActividadEvaluativaEnVivo.reconstruir(eventos).estado == (
            EstadoSesionEnVivo.FINALIZADA
        )


class TestRechazos:
    async def test_sesion_inexistente(self):
        use_case, _, canal, _, _, _ = await _escenario()

        with pytest.raises(SesionNoExiste):
            await use_case.execute(uuid4())

        assert canal.publicados == []

    async def test_sesion_en_espera(self):
        use_case, event_store, canal, sesion, _, _ = await _escenario(iniciada=False)

        with pytest.raises(SesionNoEnCurso):
            await use_case.execute(sesion.id)

        assert len(await event_store.load(AGGREGATE_TYPE_SESION, sesion.id)) == 1
        assert canal.publicados == []

    async def test_pregunta_sin_cerrar(self):
        use_case, event_store, canal, sesion, _, _ = await _escenario(cerrada=False)

        with pytest.raises(PreguntaActualNoCerrada):
            await use_case.execute(sesion.id)

        assert len(await event_store.load(AGGREGATE_TYPE_SESION, sesion.id)) == 3
        assert canal.publicados == []

    async def test_ya_finalizada_no_emite_otro_evento(self):
        use_case, event_store, canal, sesion, _, _ = await _escenario()
        await use_case.execute(sesion.id)
        cantidad = len(await event_store.load(AGGREGATE_TYPE_SESION, sesion.id))
        canal.publicados.clear()

        with pytest.raises(SesionYaFinalizada):
            await use_case.execute(sesion.id)

        assert len(await event_store.load(AGGREGATE_TYPE_SESION, sesion.id)) == cantidad
        assert canal.publicados == []

    async def test_carrera_de_dos_finalizaciones_se_traduce_a_ya_finalizada(self):
        use_case, event_store, canal, sesion, _, _ = await _escenario()
        original_append = event_store.append

        async def append_con_carrera(aggregate_type, aggregate_id, expected, events):
            await original_append(aggregate_type, aggregate_id, expected, events)
            raise ConcurrenciaOptimistaError(aggregate_type, aggregate_id, expected, expected + 1)

        event_store.append = append_con_carrera  # type: ignore[method-assign]

        with pytest.raises(SesionYaFinalizada):
            await use_case.execute(sesion.id)

        assert canal.publicados == []


class TestConduccionEnVivoControllerFinalizar:
    async def test_finalizar_delega_en_el_use_case(self):
        use_case, _, _, sesion, _, _ = await _escenario()
        controller = ConduccionEnVivoController(
            mostrar_opciones=None,  # type: ignore[arg-type]
            cerrar_pregunta=None,  # type: ignore[arg-type]
            avanzar_siguiente_pregunta=None,  # type: ignore[arg-type]
            finalizar_sesion=use_case,
        )

        resultado = await controller.finalizar_sesion(sesion.id)

        assert resultado.estado == EstadoSesionEnVivo.FINALIZADA
