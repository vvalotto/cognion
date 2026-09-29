"""Tests unitarios de `CancelarSesionEnVivoUseCase` y de su método en el controller (US-ADJ-58)."""

from uuid import uuid4

import pytest

from src.actividad_evaluativa.entities.actividad_evaluativa_en_vivo import EstadoSesionEnVivo
from src.actividad_evaluativa.entities.errors import (
    ConcurrenciaOptimistaError,
    SesionNoExiste,
    SesionYaCancelada,
    SesionYaIniciada,
)
from src.actividad_evaluativa.entities.ports.event_store_port import EventoParaAlmacenar
from src.actividad_evaluativa.interface_adapters.controllers.sesiones_en_vivo_controller import (
    SesionesEnVivoController,
)
from src.actividad_evaluativa.use_cases.cancelar_sesion_en_vivo import (
    AGGREGATE_TYPE_SESION,
    CancelarSesionEnVivoUseCase,
)
from src.actividad_evaluativa.use_cases.crear_sesion_en_vivo import CrearSesionEnVivoUseCase
from tests.unit.inc3._fakes import FakeEventStore, FakePreguntaConsultaPort
from tests.unit.inc6._fakes import FakeCanalTiempoReal, FakeComisionConsultaPort


async def _escenario():
    """Crea una sesión `EnEspera` (use case real de US-6.1.2) y arma el use case de cancelar."""
    comision_id, materia_id = uuid4(), uuid4()
    comision_consulta = FakeComisionConsultaPort()
    comision_consulta.materias[comision_id] = materia_id
    pregunta_consulta = FakePreguntaConsultaPort()
    pregunta_consulta.ids_activas[materia_id] = [uuid4() for _ in range(3)]
    event_store = FakeEventStore()
    sesion = await CrearSesionEnVivoUseCase(
        comision_consulta, pregunta_consulta, event_store
    ).execute(comision_id, 3, 30)
    canal = FakeCanalTiempoReal()
    return (
        CancelarSesionEnVivoUseCase(event_store, canal, comision_consulta),
        event_store,
        canal,
        sesion,
    )


async def _sembrar(event_store: FakeEventStore, sesion_id, tipo: str, secuencia: int) -> None:
    """Agrega un evento al stream de la sesión, como si lo hubiera emitido otro comando."""
    await event_store.append(
        AGGREGATE_TYPE_SESION,
        sesion_id,
        secuencia,
        [EventoParaAlmacenar(event_type=tipo, payload={"sesion_id": str(sesion_id)})],
    )


class TestCancelar:
    async def test_persiste_el_evento_y_pasa_a_cancelada(self):
        use_case, event_store, _, sesion = await _escenario()

        resultado = await use_case.execute(sesion.id)

        assert resultado.estado == EstadoSesionEnVivo.CANCELADA
        eventos = await event_store.load(AGGREGATE_TYPE_SESION, sesion.id)
        assert [e.event_type for e in eventos] == ["SesionEnVivoCreada", "SesionEnVivoCancelada"]
        assert eventos[-1].payload["sesion_id"] == str(sesion.id)
        assert "ocurrido_en" in eventos[-1].payload

    async def test_avisa_a_los_conectados(self):
        use_case, _, canal, sesion = await _escenario()

        await use_case.execute(sesion.id)

        assert canal.publicados == [(sesion.id, {"tipo": "sesion_cancelada"})]


class TestRechazos:
    async def test_sesion_inexistente(self):
        use_case, _, canal, _ = await _escenario()

        with pytest.raises(SesionNoExiste):
            await use_case.execute(uuid4())

        assert canal.publicados == []

    async def test_sesion_iniciada_no_se_cancela(self):
        use_case, event_store, canal, sesion = await _escenario()
        await _sembrar(event_store, sesion.id, "SesionEnVivoIniciada", 1)

        with pytest.raises(SesionYaIniciada):
            await use_case.execute(sesion.id)

        assert len(await event_store.load(AGGREGATE_TYPE_SESION, sesion.id)) == 2
        assert canal.publicados == []

    async def test_cancelar_dos_veces_no_emite_otro_evento(self):
        use_case, event_store, canal, sesion = await _escenario()
        await use_case.execute(sesion.id)
        canal.publicados.clear()

        with pytest.raises(SesionYaCancelada):
            await use_case.execute(sesion.id)

        assert len(await event_store.load(AGGREGATE_TYPE_SESION, sesion.id)) == 2
        assert canal.publicados == []

    async def test_carrera_con_un_inicio_devuelve_ya_iniciada(self):
        use_case, event_store, canal, sesion = await _escenario()
        original_append = event_store.append

        async def append_con_carrera(aggregate_type, aggregate_id, expected, events):
            # El Docente inicia desde otra pestaña justo antes: ese evento gana el `sequence_number`.
            event_store.append = original_append  # type: ignore[method-assign]
            await _sembrar(event_store, aggregate_id, "SesionEnVivoIniciada", expected)
            raise ConcurrenciaOptimistaError(aggregate_type, aggregate_id, expected, expected + 1)

        event_store.append = append_con_carrera  # type: ignore[method-assign]

        with pytest.raises(SesionYaIniciada):
            await use_case.execute(sesion.id)

        assert canal.publicados == []


class TestSesionesEnVivoControllerCancelar:
    async def test_cancelar_delega_en_el_use_case(self):
        use_case, _, _, sesion = await _escenario()
        controller = SesionesEnVivoController(None, None, None, use_case)  # type: ignore[arg-type]

        resultado = await controller.cancelar(sesion.id)

        assert resultado.id == sesion.id
        assert resultado.estado == EstadoSesionEnVivo.CANCELADA
