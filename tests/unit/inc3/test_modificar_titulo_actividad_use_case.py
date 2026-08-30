from uuid import uuid4

import pytest

from src.actividad_evaluativa.entities.errors import ActividadNoExiste
from src.actividad_evaluativa.entities.ports.event_store_port import EventoParaAlmacenar
from src.actividad_evaluativa.use_cases.modificar_periodo_disponibilidad import AGGREGATE_TYPE
from src.actividad_evaluativa.use_cases.modificar_titulo_actividad import (
    ModificarTituloActividadUseCase,
)
from tests.unit.inc3._fakes import FakeEventStore
from tests.unit.inc3.test_modificar_periodo_disponibilidad_use_case import _crear_actividad, _fechas


class TestModificarTituloActividadUseCase:
    async def test_edita_el_titulo_de_una_actividad_vigente(self):
        event_store = FakeEventStore()
        apertura, cierre = _fechas()
        actividad_id = await _crear_actividad(event_store, apertura, cierre)
        use_case = ModificarTituloActividadUseCase(event_store)

        actividad = await use_case.execute(actividad_id, "Parcial 1 (final)")

        assert actividad.titulo == "Parcial 1 (final)"
        stream = await event_store.load(AGGREGATE_TYPE, actividad_id)
        assert len(stream) == 2
        assert stream[1].event_type == "TituloActividadModificado"

    async def test_edita_el_titulo_de_una_actividad_ya_cerrada(self):
        event_store = FakeEventStore()
        apertura, cierre = _fechas()
        actividad_id = await _crear_actividad(event_store, apertura, cierre)
        await event_store.append(
            AGGREGATE_TYPE,
            actividad_id,
            1,
            [EventoParaAlmacenar(event_type="ActividadEvaluativaCerrada", payload={})],
        )
        use_case = ModificarTituloActividadUseCase(event_store)

        actividad = await use_case.execute(actividad_id, "Título corregido")

        assert actividad.titulo == "Título corregido"
        assert actividad.cerrada_manualmente is True

    async def test_rechaza_actividad_inexistente(self):
        event_store = FakeEventStore()
        use_case = ModificarTituloActividadUseCase(event_store)

        with pytest.raises(ActividadNoExiste):
            await use_case.execute(uuid4(), "Título")

    async def test_titulo_vacio_es_valido(self):
        event_store = FakeEventStore()
        apertura, cierre = _fechas()
        actividad_id = await _crear_actividad(event_store, apertura, cierre)
        use_case = ModificarTituloActividadUseCase(event_store)

        actividad = await use_case.execute(actividad_id, "")

        assert actividad.titulo == ""
