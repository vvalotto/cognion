"""Tests unitarios de `IniciarSesionEnVivoUseCase` y de su método en el controller (US-6.1.4)."""

from uuid import uuid4

import pytest

from src.actividad_evaluativa.entities.actividad_evaluativa_en_vivo import EstadoSesionEnVivo
from src.actividad_evaluativa.entities.errors import (
    ConcurrenciaOptimistaError,
    SesionNoExiste,
    SesionYaIniciada,
)
from src.actividad_evaluativa.entities.ports.event_store_port import EventoParaAlmacenar
from src.actividad_evaluativa.entities.ports.pregunta_consulta_port import ContenidoPregunta
from src.actividad_evaluativa.interface_adapters.controllers.sesiones_en_vivo_controller import (
    SesionesEnVivoController,
)
from src.actividad_evaluativa.use_cases.crear_sesion_en_vivo import CrearSesionEnVivoUseCase
from src.actividad_evaluativa.use_cases.iniciar_sesion_en_vivo import (
    AGGREGATE_TYPE_SESION,
    IniciarSesionEnVivoUseCase,
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
)


async def _escenario(opciones: list[str] | None = None):
    """Crea una sesión (use case real de US-6.1.2) y arma el use case de iniciar a probar."""
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
    ).execute(comision_id, 3, 30)
    canal = FakeCanalTiempoReal()
    use_case = IniciarSesionEnVivoUseCase(event_store, pregunta_consulta, canal)
    return use_case, event_store, canal, sesion, pregunta_consulta


class TestIniciar:
    async def test_transiciona_persiste_el_segundo_evento_y_publica(self):
        use_case, event_store, canal, sesion, pregunta_consulta = await _escenario()

        resultado = await use_case.execute(sesion.id)

        assert resultado.estado == EstadoSesionEnVivo.EN_CURSO
        assert resultado.pregunta_actual_indice == 0
        stream = await event_store.load(AGGREGATE_TYPE_SESION, sesion.id)
        assert [e.event_type for e in stream] == ["SesionEnVivoCreada", "SesionEnVivoIniciada"]
        assert stream[1].sequence_number == 2
        primera = sesion.preguntas[0].pregunta_id
        assert stream[1].payload["pregunta_actual_indice"] == 0
        assert stream[1].payload["pregunta"] == {
            "pregunta_id": str(primera),
            "enunciado": pregunta_consulta.contenidos[primera].texto,
            "tipo": "verdadero_falso",
        }

    async def test_publica_solo_el_enunciado_sin_opciones(self):
        use_case, _, canal, sesion, pregunta_consulta = await _escenario(
            opciones=["a", "b", "c", "d"]
        )

        await use_case.execute(sesion.id)

        assert len(canal.publicados) == 1
        canal_sesion_id, mensaje = canal.publicados[0]
        assert canal_sesion_id == sesion.id
        assert mensaje["tipo"] == "pregunta_presentada"
        assert mensaje["pregunta_actual_indice"] == 0
        assert mensaje["pregunta"]["tipo"] == "opcion_multiple"
        assert mensaje["pregunta"]["enunciado"].startswith("Enunciado")
        assert "opciones" not in mensaje["pregunta"]
        assert "opciones" not in mensaje

    async def test_deriva_verdadero_falso_cuando_no_hay_opciones(self):
        use_case, _, canal, sesion, _ = await _escenario(opciones=None)

        await use_case.execute(sesion.id)

        assert canal.publicados[0][1]["pregunta"]["tipo"] == "verdadero_falso"

    async def test_no_exige_participantes(self):
        use_case, _, _, sesion, _ = await _escenario()

        resultado = await use_case.execute(sesion.id)

        assert resultado.estado == EstadoSesionEnVivo.EN_CURSO


class TestRechazos:
    async def test_sesion_inexistente(self):
        use_case, _, canal, _, _ = await _escenario()

        with pytest.raises(SesionNoExiste):
            await use_case.execute(uuid4())

        assert canal.publicados == []

    async def test_segundo_inicio_se_rechaza_sin_persistir_ni_publicar(self):
        use_case, event_store, canal, sesion, _ = await _escenario()
        await use_case.execute(sesion.id)

        with pytest.raises(SesionYaIniciada):
            await use_case.execute(sesion.id)

        assert len(await event_store.load(AGGREGATE_TYPE_SESION, sesion.id)) == 2
        assert len(canal.publicados) == 1

    async def test_sesion_finalizada_tambien_es_ya_iniciada(self):
        use_case, event_store, canal, sesion, _ = await _escenario()
        for secuencia, tipo in ((1, "SesionEnVivoIniciada"), (2, "SesionEnVivoFinalizada")):
            await event_store.append(
                AGGREGATE_TYPE_SESION,
                sesion.id,
                secuencia,
                [EventoParaAlmacenar(event_type=tipo, payload={"sesion_id": str(sesion.id)})],
            )

        with pytest.raises(SesionYaIniciada):
            await use_case.execute(sesion.id)

        assert canal.publicados == []

    async def test_carrera_de_dos_inicios_deja_ganar_a_uno_solo(self):
        use_case, event_store, canal, sesion, _ = await _escenario()
        original_append = event_store.append

        async def append_con_carrera(aggregate_type, aggregate_id, expected, events):
            # Otro Docente inicia justo antes: el `sequence_number` esperado ya está ocupado.
            await original_append(aggregate_type, aggregate_id, expected, events)
            raise ConcurrenciaOptimistaError(aggregate_type, aggregate_id, expected, expected + 1)

        event_store.append = append_con_carrera  # type: ignore[method-assign]

        with pytest.raises(SesionYaIniciada):
            await use_case.execute(sesion.id)

        assert canal.publicados == []


class TestSesionesEnVivoControllerIniciar:
    async def test_iniciar_delega_en_el_use_case(self):
        use_case, event_store, _, sesion, pregunta_consulta = await _escenario()
        crear = CrearSesionEnVivoUseCase(FakeComisionConsultaPort(), pregunta_consulta, event_store)
        unirse = UnirseASesionEnVivoUseCase(
            FakeEstudianteConsultaPort(),
            event_store,
            FakeParticipantesSesionQueryPort(event_store),
            FakeCanalTiempoReal(),
        )
        controller = SesionesEnVivoController(crear, unirse, use_case)

        resultado = await controller.iniciar(sesion.id)

        assert resultado.id == sesion.id
        assert resultado.estado == EstadoSesionEnVivo.EN_CURSO
