from datetime import UTC, datetime, timedelta
from uuid import uuid4

import pytest

from src.actividad_evaluativa.entities.errors import (
    ActividadNoExiste,
    EstudianteNoExiste,
    FueraDePeriodo,
)
from src.actividad_evaluativa.entities.evaluacion import EstadoEvaluacion
from src.actividad_evaluativa.entities.ports.event_store_port import EventoParaAlmacenar
from src.actividad_evaluativa.use_cases.crear_actividad_periodo_abierto import AGGREGATE_TYPE
from src.actividad_evaluativa.use_cases.iniciar_evaluacion import (
    AGGREGATE_TYPE_EVALUACION,
    IniciarEvaluacionUseCase,
)
from tests.unit.inc3._fakes import (
    FakeEstudianteConsultaPort,
    FakeEventStore,
    FakePreguntaConsultaPort,
)


def _use_case(
    estudiante_consulta: FakeEstudianteConsultaPort,
    pregunta_consulta: FakePreguntaConsultaPort,
    event_store: FakeEventStore,
) -> IniciarEvaluacionUseCase:
    return IniciarEvaluacionUseCase(estudiante_consulta, pregunta_consulta, event_store)


async def _actividad_vigente(
    event_store: FakeEventStore,
    materia_id: object,
    cantidad_preguntas: int = 10,
) -> object:
    actividad_id = uuid4()
    apertura = datetime.now(UTC) - timedelta(days=1)
    cierre = apertura + timedelta(days=7)
    await event_store.append(
        AGGREGATE_TYPE,
        actividad_id,
        0,
        [_evento_actividad_creada(actividad_id, materia_id, apertura, cierre, cantidad_preguntas)],
    )
    return actividad_id


def _evento_actividad_creada(actividad_id, materia_id, apertura, cierre, cantidad_preguntas):
    return EventoParaAlmacenar(
        event_type="ActividadEvaluativaCreada",
        payload={
            "actividad_id": str(actividad_id),
            "materia_id": str(materia_id),
            "fecha_apertura": apertura.isoformat(),
            "fecha_cierre": cierre.isoformat(),
            "cantidad_preguntas": cantidad_preguntas,
            "cantidad_intentos_permitidos": 1,
            "ocurrido_en": apertura.isoformat(),
        },
    )


class TestIniciarEvaluacionUseCase:
    async def test_crea_evaluacion_con_set_aleatorio(self):
        materia_id, estudiante_id = uuid4(), uuid4()
        event_store = FakeEventStore()
        actividad_id = await _actividad_vigente(event_store, materia_id, cantidad_preguntas=3)
        pregunta_consulta = FakePreguntaConsultaPort()
        pregunta_consulta.ids_activas[materia_id] = [uuid4() for _ in range(10)]
        estudiante_consulta = FakeEstudianteConsultaPort()
        estudiante_consulta.estudiantes.add(estudiante_id)
        use_case = _use_case(estudiante_consulta, pregunta_consulta, event_store)

        evaluacion, creada = await use_case.execute(actividad_id, estudiante_id)

        assert creada is True
        assert evaluacion.estado == EstadoEvaluacion.EN_CURSO
        assert len(evaluacion.preguntas_asignadas) == 3
        ids_asignados = {p.pregunta_id for p in evaluacion.preguntas_asignadas}
        assert ids_asignados.issubset(set(pregunta_consulta.ids_activas[materia_id]))

        stream = await event_store.load(AGGREGATE_TYPE_EVALUACION, evaluacion.id)
        assert len(stream) == 1
        assert stream[0].event_type == "EvaluacionIniciada"

    async def test_reconexion_es_idempotente_sin_nuevo_set(self):
        materia_id, estudiante_id = uuid4(), uuid4()
        event_store = FakeEventStore()
        actividad_id = await _actividad_vigente(event_store, materia_id, cantidad_preguntas=3)
        pregunta_consulta = FakePreguntaConsultaPort()
        pregunta_consulta.ids_activas[materia_id] = [uuid4() for _ in range(10)]
        estudiante_consulta = FakeEstudianteConsultaPort()
        estudiante_consulta.estudiantes.add(estudiante_id)
        use_case = _use_case(estudiante_consulta, pregunta_consulta, event_store)

        primera, primera_creada = await use_case.execute(actividad_id, estudiante_id)
        segunda, segunda_creada = await use_case.execute(actividad_id, estudiante_id)

        assert primera_creada is True
        assert segunda_creada is False
        assert segunda.id == primera.id
        assert segunda.preguntas_asignadas == primera.preguntas_asignadas

        stream = await event_store.load(AGGREGATE_TYPE_EVALUACION, primera.id)
        assert len(stream) == 1

    async def test_dos_estudiantes_reciben_sets_propios(self):
        materia_id = uuid4()
        event_store = FakeEventStore()
        actividad_id = await _actividad_vigente(event_store, materia_id, cantidad_preguntas=5)
        pregunta_consulta = FakePreguntaConsultaPort()
        pregunta_consulta.ids_activas[materia_id] = [uuid4() for _ in range(10)]
        estudiante_consulta = FakeEstudianteConsultaPort()
        estudiante_1, estudiante_2 = uuid4(), uuid4()
        estudiante_consulta.estudiantes.update({estudiante_1, estudiante_2})
        use_case = _use_case(estudiante_consulta, pregunta_consulta, event_store)

        evaluacion_1, _ = await use_case.execute(actividad_id, estudiante_1)
        evaluacion_2, _ = await use_case.execute(actividad_id, estudiante_2)

        assert evaluacion_1.id != evaluacion_2.id
        assert evaluacion_1.estudiante_id == estudiante_1
        assert evaluacion_2.estudiante_id == estudiante_2

    async def test_rechaza_estudiante_inexistente(self):
        materia_id, estudiante_id = uuid4(), uuid4()
        event_store = FakeEventStore()
        actividad_id = await _actividad_vigente(event_store, materia_id)
        pregunta_consulta = FakePreguntaConsultaPort()
        estudiante_consulta = FakeEstudianteConsultaPort()
        use_case = _use_case(estudiante_consulta, pregunta_consulta, event_store)

        with pytest.raises(EstudianteNoExiste):
            await use_case.execute(actividad_id, estudiante_id)

    async def test_rechaza_actividad_inexistente(self):
        estudiante_id = uuid4()
        event_store = FakeEventStore()
        pregunta_consulta = FakePreguntaConsultaPort()
        estudiante_consulta = FakeEstudianteConsultaPort()
        estudiante_consulta.estudiantes.add(estudiante_id)
        use_case = _use_case(estudiante_consulta, pregunta_consulta, event_store)

        with pytest.raises(ActividadNoExiste):
            await use_case.execute(uuid4(), estudiante_id)

    async def test_rechaza_antes_de_la_apertura(self):
        materia_id, estudiante_id = uuid4(), uuid4()
        event_store = FakeEventStore()
        actividad_id = uuid4()
        apertura = datetime.now(UTC) + timedelta(days=1)
        cierre = apertura + timedelta(days=7)
        await event_store.append(
            AGGREGATE_TYPE,
            actividad_id,
            0,
            [_evento_actividad_creada(actividad_id, materia_id, apertura, cierre, 10)],
        )
        pregunta_consulta = FakePreguntaConsultaPort()
        estudiante_consulta = FakeEstudianteConsultaPort()
        estudiante_consulta.estudiantes.add(estudiante_id)
        use_case = _use_case(estudiante_consulta, pregunta_consulta, event_store)

        with pytest.raises(FueraDePeriodo):
            await use_case.execute(actividad_id, estudiante_id)

    async def test_rechaza_actividad_cerrada_manualmente_aunque_este_dentro_de_la_ventana(self):
        """US-3.4.10 — cerrar manualmente (US-3.3.2) debe bloquear también nuevos inicios,

        no solo finalizar en cascada las Evaluacion EnCurso existentes.
        """
        materia_id, estudiante_id = uuid4(), uuid4()
        event_store = FakeEventStore()
        actividad_id = await _actividad_vigente(event_store, materia_id)
        await event_store.append(
            AGGREGATE_TYPE,
            actividad_id,
            1,
            [
                EventoParaAlmacenar(
                    event_type="ActividadEvaluativaCerrada",
                    payload={
                        "actividad_id": str(actividad_id),
                        "ocurrido_en": datetime.now(UTC).isoformat(),
                    },
                )
            ],
        )
        pregunta_consulta = FakePreguntaConsultaPort()
        estudiante_consulta = FakeEstudianteConsultaPort()
        estudiante_consulta.estudiantes.add(estudiante_id)
        use_case = _use_case(estudiante_consulta, pregunta_consulta, event_store)

        with pytest.raises(FueraDePeriodo):
            await use_case.execute(actividad_id, estudiante_id)

    async def test_rechaza_despues_del_cierre(self):
        materia_id, estudiante_id = uuid4(), uuid4()
        event_store = FakeEventStore()
        actividad_id = uuid4()
        cierre = datetime.now(UTC) - timedelta(days=1)
        apertura = cierre - timedelta(days=7)
        await event_store.append(
            AGGREGATE_TYPE,
            actividad_id,
            0,
            [_evento_actividad_creada(actividad_id, materia_id, apertura, cierre, 10)],
        )
        pregunta_consulta = FakePreguntaConsultaPort()
        estudiante_consulta = FakeEstudianteConsultaPort()
        estudiante_consulta.estudiantes.add(estudiante_id)
        use_case = _use_case(estudiante_consulta, pregunta_consulta, event_store)

        with pytest.raises(FueraDePeriodo):
            await use_case.execute(actividad_id, estudiante_id)
