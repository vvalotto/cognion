import uuid

import pytest

from src.actividad_evaluativa.entities.errors import ConcurrenciaOptimistaError
from src.actividad_evaluativa.entities.ports.event_store_port import EventoParaAlmacenar
from src.actividad_evaluativa.frameworks.event_store.sqlalchemy_event_store import (
    SQLAlchemyEventStore,
)

AGGREGATE_TYPE = "EjemploTest"


class TestSQLAlchemyEventStoreAppendYLoad:
    async def test_append_y_replay_de_un_stream_nuevo(self, session):
        store = SQLAlchemyEventStore(session)
        aggregate_id = uuid.uuid4()
        eventos = [
            EventoParaAlmacenar(event_type="Evento1", payload={"n": 1}),
            EventoParaAlmacenar(event_type="Evento2", payload={"n": 2}),
            EventoParaAlmacenar(event_type="Evento3", payload={"n": 3}),
        ]

        await store.append(AGGREGATE_TYPE, aggregate_id, 0, eventos)
        stream = await store.load(AGGREGATE_TYPE, aggregate_id)

        assert [e.sequence_number for e in stream] == [1, 2, 3]
        assert [e.event_type for e in stream] == ["Evento1", "Evento2", "Evento3"]
        assert [e.payload for e in stream] == [{"n": 1}, {"n": 2}, {"n": 3}]

    async def test_load_de_stream_vacio_devuelve_lista_vacia(self, session):
        store = SQLAlchemyEventStore(session)

        assert await store.load(AGGREGATE_TYPE, uuid.uuid4()) == []

    async def test_append_incremental_continua_la_secuencia(self, session):
        store = SQLAlchemyEventStore(session)
        aggregate_id = uuid.uuid4()

        await store.append(
            AGGREGATE_TYPE, aggregate_id, 0, [EventoParaAlmacenar("Evento1", {})]
        )
        await store.append(
            AGGREGATE_TYPE, aggregate_id, 1, [EventoParaAlmacenar("Evento2", {})]
        )

        stream = await store.load(AGGREGATE_TYPE, aggregate_id)
        assert [e.sequence_number for e in stream] == [1, 2]


class TestSQLAlchemyEventStoreConcurrenciaOptimista:
    async def test_rechazo_por_concurrencia_optimista(self, session):
        store = SQLAlchemyEventStore(session)
        aggregate_id = uuid.uuid4()
        await store.append(
            AGGREGATE_TYPE, aggregate_id, 0, [EventoParaAlmacenar("Evento1", {})]
        )
        await store.append(
            AGGREGATE_TYPE, aggregate_id, 1, [EventoParaAlmacenar("Evento2", {})]
        )

        with pytest.raises(ConcurrenciaOptimistaError):
            await store.append(
                AGGREGATE_TYPE, aggregate_id, 1, [EventoParaAlmacenar("EventoConflictivo", {})]
            )

        stream = await store.load(AGGREGATE_TYPE, aggregate_id)
        assert [e.event_type for e in stream] == ["Evento1", "Evento2"]

    async def test_append_sobre_stream_nuevo_con_expected_distinto_de_cero_falla(self, session):
        store = SQLAlchemyEventStore(session)

        with pytest.raises(ConcurrenciaOptimistaError):
            await store.append(
                AGGREGATE_TYPE, uuid.uuid4(), 1, [EventoParaAlmacenar("Evento1", {})]
            )


class TestSQLAlchemyEventStoreAtomicidad:
    async def test_atomicidad_del_append_multiple(self, session):
        store = SQLAlchemyEventStore(session)
        aggregate_id = uuid.uuid4()
        eventos_con_payload_no_serializable = [
            EventoParaAlmacenar(event_type="Evento1", payload={"ok": 1}),
            EventoParaAlmacenar(event_type="Evento2", payload={"malo": {1, 2, 3}}),
        ]

        with pytest.raises(Exception):
            await store.append(AGGREGATE_TYPE, aggregate_id, 0, eventos_con_payload_no_serializable)

        await session.rollback()
        stream = await store.load(AGGREGATE_TYPE, aggregate_id)
        assert stream == []


class TestSQLAlchemyEventStoreAislamientoEntreStreams:
    async def test_load_no_incluye_eventos_de_otro_stream(self, session):
        store = SQLAlchemyEventStore(session)
        stream_a = uuid.uuid4()
        stream_b = uuid.uuid4()
        await store.append(AGGREGATE_TYPE, stream_a, 0, [EventoParaAlmacenar("EventoA", {})])
        await store.append(AGGREGATE_TYPE, stream_b, 0, [EventoParaAlmacenar("EventoB", {})])

        eventos_a = await store.load(AGGREGATE_TYPE, stream_a)

        assert [e.event_type for e in eventos_a] == ["EventoA"]

    async def test_load_no_incluye_eventos_de_otro_aggregate_type(self, session):
        store = SQLAlchemyEventStore(session)
        aggregate_id = uuid.uuid4()
        await store.append(
            "OtroAggregateType", aggregate_id, 0, [EventoParaAlmacenar("EventoOtroTipo", {})]
        )

        assert await store.load(AGGREGATE_TYPE, aggregate_id) == []
