"""Tests unitarios de `UnirseASesionEnVivoUseCase` y de su método en el controller (US-6.1.3)."""

from datetime import UTC, datetime
from uuid import uuid4

import pytest

from src.actividad_evaluativa.entities.errors import (
    ConcurrenciaOptimistaError,
    EstudianteNoExiste,
    SesionNoExiste,
    SesionYaFinalizada,
)
from src.actividad_evaluativa.entities.participacion_en_vivo import ParticipacionEnVivo
from src.actividad_evaluativa.entities.ports.event_store_port import EventoParaAlmacenar
from src.actividad_evaluativa.interface_adapters.controllers.sesiones_en_vivo_controller import (
    SesionesEnVivoController,
)
from src.actividad_evaluativa.use_cases.crear_sesion_en_vivo import CrearSesionEnVivoUseCase
from src.actividad_evaluativa.use_cases.iniciar_sesion_en_vivo import (
    IniciarSesionEnVivoUseCase,
)
from src.actividad_evaluativa.use_cases.unirse_a_sesion_en_vivo import (
    AGGREGATE_TYPE_PARTICIPACION,
    AGGREGATE_TYPE_SESION,
    UnirseASesionEnVivoUseCase,
)
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


async def _escenario():
    """Arma una sesión ya creada (por el use case real de US-6.1.2) y el use case a probar."""
    comision_id, materia_id = uuid4(), uuid4()
    comision_consulta = FakeComisionConsultaPort()
    comision_consulta.materias[comision_id] = materia_id
    pregunta_consulta = FakePreguntaConsultaPort()
    pregunta_consulta.ids_activas[materia_id] = [uuid4() for _ in range(10)]
    event_store = FakeEventStore()
    sesion = await CrearSesionEnVivoUseCase(
        comision_consulta, pregunta_consulta, event_store
    ).execute(comision_id, 5, 30)

    estudiantes = FakeEstudianteConsultaPort()
    canal = FakeCanalTiempoReal()
    proyecciones = FakeProyeccionesEnVivo()
    use_case = UnirseASesionEnVivoUseCase(
        estudiantes,
        event_store,
        FakeParticipantesSesionQueryPort(event_store),
        canal,
        proyecciones,
    )
    return use_case, event_store, estudiantes, canal, sesion


async def _sembrar_evento_de_sesion(event_store, sesion_id, tipo: str, secuencia: int) -> None:
    """Siembra un evento posterior en el stream de la sesión — `US-6.1.4`/Iteración 2 todavía no
    los emiten por API, así que los tests los agregan directamente.
    """
    await event_store.append(
        AGGREGATE_TYPE_SESION,
        sesion_id,
        secuencia - 1,
        [
            EventoParaAlmacenar(
                event_type=tipo,
                payload={"sesion_id": str(sesion_id), "ocurrido_en": datetime.now(UTC).isoformat()},
            )
        ],
    )


class TestUnirse:
    async def test_une_en_espera_persiste_el_evento_y_publica(self):
        use_case, event_store, estudiantes, canal, sesion = await _escenario()
        estudiante_id = uuid4()
        estudiantes.estudiantes.add(estudiante_id)

        participacion = await use_case.execute(sesion.id, estudiante_id)

        assert participacion.sesion_id == sesion.id
        assert participacion.estudiante_id == estudiante_id
        assert participacion.respuestas == []
        stream = await event_store.load(AGGREGATE_TYPE_PARTICIPACION, participacion.id)
        assert len(stream) == 1
        assert stream[0].sequence_number == 1
        assert stream[0].event_type == "EstudianteUnido"
        assert stream[0].payload["sesion_id"] == str(sesion.id)
        assert stream[0].payload["estudiante_id"] == str(estudiante_id)

        assert len(canal.publicados) == 1
        canal_sesion_id, mensaje = canal.publicados[0]
        assert canal_sesion_id == sesion.id
        assert mensaje["tipo"] == "participantes_actualizados"
        assert mensaje["cantidad"] == 1
        assert mensaje["participantes"][0]["estudiante_id"] == str(estudiante_id)

    async def test_union_tardia_con_la_sesion_en_curso(self):
        use_case, event_store, estudiantes, _, sesion = await _escenario()
        await _sembrar_evento_de_sesion(event_store, sesion.id, "SesionEnVivoIniciada", 2)
        estudiante_id = uuid4()
        estudiantes.estudiantes.add(estudiante_id)

        participacion = await use_case.execute(sesion.id, estudiante_id)

        assert participacion.respuestas == []
        stream = await event_store.load(AGGREGATE_TYPE_PARTICIPACION, participacion.id)
        assert len(stream) == 1

    async def test_varios_estudiantes_se_acumulan_en_la_lista_publicada(self):
        use_case, _, estudiantes, canal, sesion = await _escenario()
        ids = [uuid4() for _ in range(3)]
        estudiantes.estudiantes.update(ids)

        for estudiante_id in ids:
            await use_case.execute(sesion.id, estudiante_id)

        assert [m["cantidad"] for _, m in canal.publicados] == [1, 2, 3]
        ultimos = {p["estudiante_id"] for p in canal.publicados[-1][1]["participantes"]}
        assert ultimos == {str(i) for i in ids}


class TestIdempotencia:
    async def test_unirse_dos_veces_no_crea_un_segundo_evento(self):
        use_case, event_store, estudiantes, _, sesion = await _escenario()
        estudiante_id = uuid4()
        estudiantes.estudiantes.add(estudiante_id)

        primera = await use_case.execute(sesion.id, estudiante_id)
        segunda = await use_case.execute(sesion.id, estudiante_id)

        assert segunda.id == primera.id
        assert segunda.unido_en == primera.unido_en
        stream = await event_store.load(AGGREGATE_TYPE_PARTICIPACION, primera.id)
        assert len(stream) == 1

    async def test_el_caso_idempotente_tambien_publica_sin_cambiar_el_conteo(self):
        use_case, _, estudiantes, canal, sesion = await _escenario()
        estudiante_id = uuid4()
        estudiantes.estudiantes.add(estudiante_id)

        await use_case.execute(sesion.id, estudiante_id)
        await use_case.execute(sesion.id, estudiante_id)

        assert [m["cantidad"] for _, m in canal.publicados] == [1, 1]

    async def test_concurrencia_al_insertar_devuelve_la_participacion_ganadora(self):
        use_case, event_store, estudiantes, _, sesion = await _escenario()
        estudiante_id = uuid4()
        estudiantes.estudiantes.add(estudiante_id)
        ganadora = ParticipacionEnVivo.unirse(sesion.id, estudiante_id)

        original_append = event_store.append

        async def append_con_carrera(aggregate_type, aggregate_id, expected, events):
            if aggregate_type == AGGREGATE_TYPE_PARTICIPACION:
                # Otra invocación concurrente inserta primero el mismo evento...
                await original_append(aggregate_type, aggregate_id, expected, events)
                # ...y esta segunda inserción choca con el `sequence_number` ya ocupado.
                raise ConcurrenciaOptimistaError(aggregate_type, aggregate_id, expected, 1)
            await original_append(aggregate_type, aggregate_id, expected, events)

        event_store.append = append_con_carrera  # type: ignore[method-assign]

        participacion = await use_case.execute(sesion.id, estudiante_id)

        assert participacion.id == ganadora.id
        stream = await event_store.load(AGGREGATE_TYPE_PARTICIPACION, ganadora.id)
        assert len(stream) == 1


class TestRechazos:
    async def test_sesion_inexistente(self):
        use_case, event_store, estudiantes, canal, _ = await _escenario()
        estudiante_id = uuid4()
        estudiantes.estudiantes.add(estudiante_id)

        with pytest.raises(SesionNoExiste):
            await use_case.execute(uuid4(), estudiante_id)

        assert canal.publicados == []

    async def test_sesion_finalizada_no_persiste_ni_publica(self):
        use_case, event_store, estudiantes, canal, sesion = await _escenario()
        await _sembrar_evento_de_sesion(event_store, sesion.id, "SesionEnVivoIniciada", 2)
        await _sembrar_evento_de_sesion(event_store, sesion.id, "SesionEnVivoFinalizada", 3)
        estudiante_id = uuid4()
        estudiantes.estudiantes.add(estudiante_id)

        with pytest.raises(SesionYaFinalizada):
            await use_case.execute(sesion.id, estudiante_id)

        participacion_id = ParticipacionEnVivo.id_para(sesion.id, estudiante_id)
        assert await event_store.load(AGGREGATE_TYPE_PARTICIPACION, participacion_id) == []
        assert canal.publicados == []

    async def test_estudiante_ya_unido_tambien_es_rechazado_si_la_sesion_termino(self):
        use_case, event_store, estudiantes, _, sesion = await _escenario()
        estudiante_id = uuid4()
        estudiantes.estudiantes.add(estudiante_id)
        await use_case.execute(sesion.id, estudiante_id)
        await _sembrar_evento_de_sesion(event_store, sesion.id, "SesionEnVivoIniciada", 2)
        await _sembrar_evento_de_sesion(event_store, sesion.id, "SesionEnVivoFinalizada", 3)

        with pytest.raises(SesionYaFinalizada):
            await use_case.execute(sesion.id, estudiante_id)

    async def test_estudiante_inexistente(self):
        use_case, _, _, canal, sesion = await _escenario()

        with pytest.raises(EstudianteNoExiste):
            await use_case.execute(sesion.id, uuid4())

        assert canal.publicados == []


class TestSesionesEnVivoControllerUnirse:
    async def test_unirse_delega_en_el_use_case(self):
        use_case, _, estudiantes, _, sesion = await _escenario()
        estudiante_id = uuid4()
        estudiantes.estudiantes.add(estudiante_id)
        iniciar = IniciarSesionEnVivoUseCase(
            FakeEventStore(), FakePreguntaConsultaPort(), FakeCanalTiempoReal()
        )
        controller = SesionesEnVivoController(_crear_sesion_stub(), use_case, iniciar)

        participacion = await controller.unirse(sesion.id, estudiante_id)

        assert participacion.sesion_id == sesion.id
        assert participacion.estudiante_id == estudiante_id


def _crear_sesion_stub() -> CrearSesionEnVivoUseCase:
    """El controller exige ambos use cases; este test solo ejercita `unirse`."""
    return CrearSesionEnVivoUseCase(
        FakeComisionConsultaPort(), FakePreguntaConsultaPort(), FakeEventStore()
    )


class TestProyeccionRanking:
    async def test_unirse_deja_al_participante_en_el_ranking_con_cero_puntos(self):
        use_case, _, estudiantes, _, sesion = await _escenario()
        estudiante_id = uuid4()
        estudiantes.estudiantes.add(estudiante_id)

        await use_case.execute(sesion.id, estudiante_id)

        ranking = await use_case._proyecciones.ranking(sesion.id)
        assert [(r.estudiante_id, r.puntaje_acumulado) for r in ranking] == [(estudiante_id, 0)]

    async def test_reunirse_no_reinicia_ni_duplica_la_fila(self):
        use_case, _, estudiantes, _, sesion = await _escenario()
        estudiante_id = uuid4()
        estudiantes.estudiantes.add(estudiante_id)
        await use_case.execute(sesion.id, estudiante_id)
        await use_case._proyecciones.registrar_respuesta(
            sesion.id, estudiante_id, uuid4(), "1", 1500
        )

        await use_case.execute(sesion.id, estudiante_id)

        ranking = await use_case._proyecciones.ranking(sesion.id)
        assert [(r.estudiante_id, r.puntaje_acumulado) for r in ranking] == [(estudiante_id, 1500)]

    async def test_al_perder_la_carrera_descarta_la_proyeccion_pendiente(self):
        use_case, event_store, estudiantes, _, sesion = await _escenario()
        estudiante_id = uuid4()
        estudiantes.estudiantes.add(estudiante_id)
        original = event_store.append

        async def append_que_pierde_la_carrera(aggregate_type, aggregate_id, esperado, eventos):
            if aggregate_type == AGGREGATE_TYPE_PARTICIPACION:
                await original(aggregate_type, aggregate_id, esperado, eventos)
                raise ConcurrenciaOptimistaError(
                    aggregate_type, aggregate_id, esperado, esperado + 1
                )
            await original(aggregate_type, aggregate_id, esperado, eventos)

        event_store.append = append_que_pierde_la_carrera

        participacion = await use_case.execute(sesion.id, estudiante_id)

        assert use_case._proyecciones.descartes == 1
        assert participacion.estudiante_id == estudiante_id
