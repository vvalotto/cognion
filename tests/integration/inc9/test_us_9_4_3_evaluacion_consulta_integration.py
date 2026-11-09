"""Caracterización de `EvaluacionConsultaPortInProcess` de Identidad (US-9.4.3, ADR-026).

Fija el comportamiento del adaptador contra PostgreSQL real; debe dar lo mismo antes y después de que
deje de leer `EventoModel` de Actividad Evaluativa. Requiere base descartable (`DATABASE_URL` inline).
"""

from __future__ import annotations

import uuid

from src.actividad_evaluativa.entities.ports.event_store_port import EventoParaAlmacenar
from src.actividad_evaluativa.frameworks.event_store.sqlalchemy_event_store import (
    SQLAlchemyEventStore,
)
from src.identidad.frameworks.adapters.evaluacion_consulta_port_in_process import (
    EvaluacionConsultaPortInProcess,
)


async def _evento(session, aggregate_type: str, event_type: str, estudiante_id: uuid.UUID) -> None:
    await SQLAlchemyEventStore(session).append(
        aggregate_type,
        uuid.uuid4(),
        0,
        [EventoParaAlmacenar(event_type, {"estudiante_id": str(estudiante_id)})],
    )


class TestTieneEvaluaciones:
    async def test_estudiante_sin_evaluaciones(self, session):
        assert (
            await EvaluacionConsultaPortInProcess(session).tiene_evaluaciones(uuid.uuid4()) is False
        )

    async def test_estudiante_con_una_evaluacion_iniciada(self, session):
        estudiante_id = uuid.uuid4()
        await _evento(session, "Evaluacion", "EvaluacionIniciada", estudiante_id)

        assert await EvaluacionConsultaPortInProcess(session).tiene_evaluaciones(estudiante_id)

    async def test_las_evaluaciones_de_otro_estudiante_no_cuentan(self, session):
        await _evento(session, "Evaluacion", "EvaluacionIniciada", uuid.uuid4())

        assert not await EvaluacionConsultaPortInProcess(session).tiene_evaluaciones(uuid.uuid4())

    async def test_otro_tipo_de_evento_no_cuenta(self, session):
        estudiante_id = uuid.uuid4()
        await _evento(session, "Evaluacion", "RespuestaRegistrada", estudiante_id)

        assert not await EvaluacionConsultaPortInProcess(session).tiene_evaluaciones(estudiante_id)

    async def test_otro_agregado_no_cuenta(self, session):
        estudiante_id = uuid.uuid4()
        await _evento(session, "ParticipacionEnVivo", "EvaluacionIniciada", estudiante_id)

        assert not await EvaluacionConsultaPortInProcess(session).tiene_evaluaciones(estudiante_id)
