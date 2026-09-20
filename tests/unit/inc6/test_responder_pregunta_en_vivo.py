"""Tests unitarios de la respuesta en vivo: aggregate, evento, use case y controller (US-6.2.4)."""

from datetime import UTC, datetime, timedelta
from uuid import uuid4

import pytest

from src.actividad_evaluativa.entities.actividad_evaluativa_en_vivo import (
    ActividadEvaluativaEnVivo,
    EstadoSesionEnVivo,
)
from src.actividad_evaluativa.entities.errors import (
    ConcurrenciaOptimistaError,
    OpcionesNoMostradasTodavia,
    ParticipacionNoExiste,
    PreguntaNoActual,
    PreguntaYaCerrada,
    RespuestaYaRegistrada,
    SesionNoEnCurso,
    SesionNoExiste,
    TiempoAgotado,
)
from src.actividad_evaluativa.entities.evaluacion import PreguntaAsignada
from src.actividad_evaluativa.entities.eventos_en_vivo import RespuestaEnVivoRegistrada
from src.actividad_evaluativa.entities.participacion_en_vivo import (
    ParticipacionEnVivo,
    RespuestaEnVivo,
)
from src.actividad_evaluativa.entities.ports.event_store_port import (
    EventoAlmacenado,
    EventoParaAlmacenar,
)
from src.actividad_evaluativa.entities.ports.pregunta_consulta_port import ContenidoPregunta
from src.actividad_evaluativa.entities.puntaje_en_vivo import NivelesDePregunta, NivelPregunta
from src.actividad_evaluativa.interface_adapters.controllers.participaciones_en_vivo_controller import (
    ParticipacionesEnVivoController,
)
from src.actividad_evaluativa.use_cases.crear_sesion_en_vivo import CrearSesionEnVivoUseCase
from src.actividad_evaluativa.use_cases.iniciar_sesion_en_vivo import IniciarSesionEnVivoUseCase
from src.actividad_evaluativa.use_cases.responder_pregunta_en_vivo import (
    AGGREGATE_TYPE_PARTICIPACION,
    AGGREGATE_TYPE_SESION,
    ResponderPreguntaEnVivoUseCase,
    ResultadoRespuestaEnVivo,
    _opcion_de,
)
from src.actividad_evaluativa.use_cases.unirse_a_sesion_en_vivo import UnirseASesionEnVivoUseCase
from tests.unit.inc3._fakes import (
    FakeEstudianteConsultaPort,
    FakeEventStore,
    FakePreguntaConsultaPort,
)
from tests.unit.inc6._fakes import (
    FakeCanalTiempoReal,
    FakeComisionConsultaPort,
    FakeParticipantesSesionQueryPort,
    FakeProyeccionesEnVivo,
)

LIMITE = 30


def _sesion_en_curso(mostrada_hace: float | None = 5.0) -> ActividadEvaluativaEnVivo:
    """Sesión `EnCurso` en la pregunta 0; opciones mostradas hace `mostrada_hace` segundos."""
    ahora = datetime.now(UTC)
    return ActividadEvaluativaEnVivo(
        id=uuid4(),
        comision_id=uuid4(),
        materia_id=uuid4(),
        preguntas=[PreguntaAsignada(uuid4(), 1), PreguntaAsignada(uuid4(), 2)],
        tiempo_limite_por_pregunta_segundos=LIMITE,
        estado=EstadoSesionEnVivo.EN_CURSO,
        pregunta_actual_indice=0,
        opciones_mostradas=mostrada_hace is not None,
        opciones_mostradas_en=(
            None if mostrada_hace is None else ahora - timedelta(seconds=mostrada_hace)
        ),
    )


class TestValidarParaResponder:
    def test_devuelve_el_tiempo_desde_que_se_mostraron_las_opciones(self):
        sesion = _sesion_en_curso(mostrada_hace=5.0)
        ahora = sesion.opciones_mostradas_en + timedelta(seconds=7.5)

        tiempo = sesion.validar_para_responder(sesion.preguntas[0].pregunta_id, ahora)

        assert tiempo == 7.5

    @pytest.mark.parametrize(
        "estado", [EstadoSesionEnVivo.EN_ESPERA, EstadoSesionEnVivo.FINALIZADA]
    )
    def test_rechaza_si_no_esta_en_curso(self, estado):
        sesion = _sesion_en_curso()
        sesion.estado = estado

        with pytest.raises(SesionNoEnCurso):
            sesion.validar_para_responder(sesion.preguntas[0].pregunta_id, datetime.now(UTC))

    def test_rechaza_si_no_es_la_pregunta_actual(self):
        sesion = _sesion_en_curso()

        with pytest.raises(PreguntaNoActual):
            sesion.validar_para_responder(sesion.preguntas[1].pregunta_id, datetime.now(UTC))

    def test_rechaza_si_la_pregunta_ya_fue_cerrada(self):
        sesion = _sesion_en_curso()
        sesion.pregunta_actual_cerrada = True

        with pytest.raises(PreguntaYaCerrada):
            sesion.validar_para_responder(sesion.preguntas[0].pregunta_id, datetime.now(UTC))

    def test_rechaza_si_las_opciones_no_se_mostraron(self):
        sesion = _sesion_en_curso(mostrada_hace=None)

        with pytest.raises(OpcionesNoMostradasTodavia):
            sesion.validar_para_responder(sesion.preguntas[0].pregunta_id, datetime.now(UTC))

    def test_rechaza_por_tiempo_agotado_aunque_no_este_cerrada(self):
        sesion = _sesion_en_curso(mostrada_hace=LIMITE + 5)

        with pytest.raises(TiempoAgotado) as exc:
            sesion.validar_para_responder(sesion.preguntas[0].pregunta_id, datetime.now(UTC))

        assert exc.value.tiempo_respuesta_segundos > LIMITE

    def test_acepta_justo_en_el_limite(self):
        sesion = _sesion_en_curso()
        ahora = sesion.opciones_mostradas_en + timedelta(seconds=LIMITE)

        assert sesion.validar_para_responder(sesion.preguntas[0].pregunta_id, ahora) == LIMITE


class TestParticipacionResponder:
    def test_registra_la_respuesta_y_suma_el_puntaje(self):
        participacion = ParticipacionEnVivo.unirse(uuid4(), uuid4())
        p1, p2 = uuid4(), uuid4()

        participacion.responder(p1, {"opcion_indice": 1}, True, 3.0, 1200)
        participacion.responder(p2, {"valor": False}, False, 4.0, 0)

        assert len(participacion.respuestas) == 2
        assert participacion.puntaje_acumulado == 1200

    def test_un_solo_intento_por_pregunta(self):
        participacion = ParticipacionEnVivo.unirse(uuid4(), uuid4())
        pregunta_id = uuid4()
        participacion.responder(pregunta_id, {"opcion_indice": 0}, True, 1.0, 1000)

        with pytest.raises(RespuestaYaRegistrada):
            participacion.responder(pregunta_id, {"opcion_indice": 1}, False, 2.0, 0)

        assert participacion.puntaje_acumulado == 1000
        assert len(participacion.respuestas) == 1

    def test_reconstruir_aplica_las_respuestas_del_stream(self):
        sesion_id, estudiante_id, pregunta_id = uuid4(), uuid4(), uuid4()
        ahora = datetime.now(UTC)
        eventos = [
            EventoAlmacenado(
                1,
                "EstudianteUnido",
                {
                    "sesion_id": str(sesion_id),
                    "estudiante_id": str(estudiante_id),
                    "unido_en": ahora.isoformat(),
                },
                ahora,
            ),
            EventoAlmacenado(
                2,
                "RespuestaEnVivoRegistrada",
                {
                    "pregunta_id": str(pregunta_id),
                    "contenido": {"valor": True},
                    "es_correcta": True,
                    "tiempo_respuesta_segundos": 2.5,
                    "puntaje": 1500,
                },
                ahora,
            ),
        ]

        participacion = ParticipacionEnVivo.reconstruir(eventos)

        assert participacion.respuestas == [
            RespuestaEnVivo(pregunta_id, {"valor": True}, True, 2.5, 1500)
        ]
        assert participacion.puntaje_acumulado == 1500

    def test_evento_desde_respuesta_copia_los_campos(self):
        participacion = ParticipacionEnVivo.unirse(uuid4(), uuid4())
        pregunta_id = uuid4()
        respuesta = participacion.responder(pregunta_id, {"opcion_indice": 2}, True, 3.0, 900)

        evento = RespuestaEnVivoRegistrada.desde_respuesta(participacion, respuesta)

        assert (evento.sesion_id, evento.estudiante_id) == (
            participacion.sesion_id,
            participacion.estudiante_id,
        )
        assert (evento.pregunta_id, evento.contenido, evento.es_correcta) == (
            pregunta_id,
            {"opcion_indice": 2},
            True,
        )
        assert (evento.tiempo_respuesta_segundos, evento.puntaje) == (3.0, 900)


class TestOpcionDe:
    def test_opcion_multiple_usa_el_indice(self):
        assert _opcion_de({"opcion_indice": 2}) == "2"

    def test_verdadero_falso(self):
        assert _opcion_de({"valor": True}) == "verdadero"
        assert _opcion_de({"valor": False}) == "falso"


async def _escenario(mostrar: str | None = "ahora", unirse: bool = True):
    """Crea, inicia y (según `mostrar`) muestra las opciones de una sesión; une a un Estudiante.

    `mostrar`: `"ahora"` (a tiempo), `"viejo"` (fuera del límite) o `None` (solo enunciado).
    """
    comision_id, materia_id, estudiante_id = uuid4(), uuid4(), uuid4()
    comision_consulta = FakeComisionConsultaPort()
    comision_consulta.materias[comision_id] = materia_id
    pregunta_consulta = FakePreguntaConsultaPort()
    ids = [uuid4() for _ in range(6)]
    pregunta_consulta.ids_activas[materia_id] = ids
    for i, pregunta_id in enumerate(ids):
        pregunta_consulta.contenidos[pregunta_id] = ContenidoPregunta(f"P{i}", ["A", "B"])
    event_store = FakeEventStore()
    canal = FakeCanalTiempoReal()
    proyecciones = FakeProyeccionesEnVivo()
    estudiantes = FakeEstudianteConsultaPort()
    estudiantes.estudiantes.add(estudiante_id)

    sesion = await CrearSesionEnVivoUseCase(
        comision_consulta, pregunta_consulta, event_store
    ).execute(comision_id, 3, LIMITE)
    await IniciarSesionEnVivoUseCase(event_store, pregunta_consulta, canal).execute(sesion.id)
    pregunta_actual = sesion.preguntas[0].pregunta_id
    if mostrar is not None:
        hace = timedelta(seconds=LIMITE + 60 if mostrar == "viejo" else 2)
        await event_store.append(
            AGGREGATE_TYPE_SESION,
            sesion.id,
            2,
            [
                EventoParaAlmacenar(
                    "OpcionesEnVivoMostradas",
                    {
                        "sesion_id": str(sesion.id),
                        "pregunta_actual_indice": 0,
                        "pregunta_id": str(pregunta_actual),
                        "opciones": ["A", "B"],
                        "ocurrido_en": (datetime.now(UTC) - hace).isoformat(),
                    },
                )
            ],
        )
    if unirse:
        await UnirseASesionEnVivoUseCase(
            estudiantes,
            event_store,
            FakeParticipantesSesionQueryPort(event_store),
            canal,
            proyecciones,
        ).execute(sesion.id, estudiante_id)
    canal.publicados.clear()
    use_case = ResponderPreguntaEnVivoUseCase(
        event_store, pregunta_consulta, proyecciones, proyecciones, canal
    )
    return use_case, event_store, canal, proyecciones, pregunta_consulta, sesion, estudiante_id


class TestResponderUseCase:
    async def test_respuesta_correcta_persiste_puntua_y_publica_el_conteo(self):
        use_case, store, canal, proy, consulta, sesion, est = await _escenario()
        pregunta_id = sesion.preguntas[0].pregunta_id
        consulta.correcciones[pregunta_id] = True
        consulta.niveles[pregunta_id] = NivelesDePregunta(NivelPregunta.MEDIO, NivelPregunta.ALTO)

        resultado = await use_case.execute(sesion.id, est, pregunta_id, {"opcion_indice": 1})

        assert resultado.es_correcta is True
        assert 0 < resultado.puntaje <= 3000 and resultado.puntaje_acumulado == resultado.puntaje
        eventos = await store.load(
            AGGREGATE_TYPE_PARTICIPACION, ParticipacionEnVivo.id_para(sesion.id, est)
        )
        assert eventos[-1].event_type == "RespuestaEnVivoRegistrada"
        assert eventos[-1].payload["tiempo_respuesta_segundos"] >= 2
        assert proy.puntajes[(sesion.id, est)] == resultado.puntaje
        assert proy.conteos[(sesion.id, pregunta_id, "1")] == 1
        assert canal.publicados == [
            (
                sesion.id,
                {
                    "tipo": "conteo_respuestas_actualizado",
                    "pregunta_actual_indice": 0,
                    "cantidad_respuestas": 1,
                },
            )
        ]

    async def test_respuesta_incorrecta_puntua_cero(self):
        use_case, _, _, proy, _, sesion, est = await _escenario()

        resultado = await use_case.execute(
            sesion.id, est, sesion.preguntas[0].pregunta_id, {"opcion_indice": 0}
        )

        assert resultado == ResultadoRespuestaEnVivo(False, 0, 0)
        assert proy.puntajes[(sesion.id, est)] == 0

    async def test_verdadero_falso_registra_la_opcion_textual(self):
        use_case, _, _, proy, _, sesion, est = await _escenario()
        pregunta_id = sesion.preguntas[0].pregunta_id

        await use_case.execute(sesion.id, est, pregunta_id, {"valor": True})

        assert proy.conteos[(sesion.id, pregunta_id, "verdadero")] == 1

    async def test_segundo_intento_se_rechaza_sin_cambiar_el_puntaje(self):
        use_case, _, canal, proy, consulta, sesion, est = await _escenario()
        pregunta_id = sesion.preguntas[0].pregunta_id
        consulta.correcciones[pregunta_id] = True
        await use_case.execute(sesion.id, est, pregunta_id, {"opcion_indice": 1})
        puntaje = proy.puntajes[(sesion.id, est)]
        canal.publicados.clear()

        with pytest.raises(RespuestaYaRegistrada):
            await use_case.execute(sesion.id, est, pregunta_id, {"opcion_indice": 0})

        assert proy.puntajes[(sesion.id, est)] == puntaje
        assert canal.publicados == []

    async def test_carrera_de_doble_envio_descarta_la_proyeccion(self, monkeypatch):
        use_case, store, canal, proy, _, sesion, est = await _escenario()

        async def _perder_la_carrera(*_args, **_kwargs):
            raise ConcurrenciaOptimistaError(AGGREGATE_TYPE_PARTICIPACION, est, 1, 2)

        monkeypatch.setattr(store, "append", _perder_la_carrera)

        with pytest.raises(RespuestaYaRegistrada):
            await use_case.execute(
                sesion.id, est, sesion.preguntas[0].pregunta_id, {"opcion_indice": 1}
            )

        assert proy.descartes == 1
        assert canal.publicados == []

    async def test_sesion_inexistente(self):
        use_case, *_ = await _escenario()

        with pytest.raises(SesionNoExiste):
            await use_case.execute(uuid4(), uuid4(), uuid4(), {"valor": True})

    async def test_estudiante_que_no_se_unio(self):
        use_case, _, _, _, _, sesion, _ = await _escenario(unirse=False)

        with pytest.raises(ParticipacionNoExiste):
            await use_case.execute(
                sesion.id, uuid4(), sesion.preguntas[0].pregunta_id, {"valor": True}
            )

    async def test_opciones_no_mostradas(self):
        use_case, _, canal, proy, _, sesion, est = await _escenario(mostrar=None)

        with pytest.raises(OpcionesNoMostradasTodavia):
            await use_case.execute(
                sesion.id, est, sesion.preguntas[0].pregunta_id, {"opcion_indice": 0}
            )

        assert canal.publicados == [] and proy.conteos == {}

    async def test_tiempo_agotado(self):
        use_case, _, _, proy, _, sesion, est = await _escenario(mostrar="viejo")

        with pytest.raises(TiempoAgotado):
            await use_case.execute(
                sesion.id, est, sesion.preguntas[0].pregunta_id, {"opcion_indice": 0}
            )

        assert proy.conteos == {}

    async def test_pregunta_que_no_es_la_actual(self):
        use_case, _, _, _, _, sesion, est = await _escenario()

        with pytest.raises(PreguntaNoActual):
            await use_case.execute(
                sesion.id, est, sesion.preguntas[1].pregunta_id, {"opcion_indice": 0}
            )


class TestControllerResponder:
    async def test_delega_en_el_caso_de_uso(self):
        use_case, _, _, _, _, sesion, est = await _escenario()
        controller = ParticipacionesEnVivoController(use_case)

        resultado = await controller.responder(
            sesion.id, est, sesion.preguntas[0].pregunta_id, {"opcion_indice": 0}
        )

        assert isinstance(resultado, ResultadoRespuestaEnVivo)
