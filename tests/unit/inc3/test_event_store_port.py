from datetime import UTC, datetime

import pytest

from src.actividad_evaluativa.entities.ports.event_store_port import (
    EventoAlmacenado,
    EventoParaAlmacenar,
)


class TestEventoParaAlmacenar:
    def test_guarda_event_type_y_payload(self):
        evento = EventoParaAlmacenar(event_type="EjemploCreado", payload={"clave": "valor"})

        assert evento.event_type == "EjemploCreado"
        assert evento.payload == {"clave": "valor"}

    def test_es_inmutable(self):
        evento = EventoParaAlmacenar(event_type="EjemploCreado", payload={})

        with pytest.raises(AttributeError):
            evento.event_type = "Otro"


class TestEventoAlmacenado:
    def test_guarda_todos_los_campos(self):
        ahora = datetime.now(UTC)

        evento = EventoAlmacenado(
            sequence_number=1,
            event_type="EjemploCreado",
            payload={"clave": "valor"},
            occurred_at=ahora,
        )

        assert evento.sequence_number == 1
        assert evento.event_type == "EjemploCreado"
        assert evento.payload == {"clave": "valor"}
        assert evento.occurred_at == ahora

    def test_es_inmutable(self):
        evento = EventoAlmacenado(
            sequence_number=1,
            event_type="EjemploCreado",
            payload={},
            occurred_at=datetime.now(UTC),
        )

        with pytest.raises(AttributeError):
            evento.sequence_number = 2

    def test_compara_por_valor(self):
        ahora = datetime.now(UTC)
        base = {"sequence_number": 1, "event_type": "X", "payload": {}, "occurred_at": ahora}

        assert EventoAlmacenado(**base) == EventoAlmacenado(**base)
        assert EventoAlmacenado(**base) != EventoAlmacenado(**{**base, "sequence_number": 2})
