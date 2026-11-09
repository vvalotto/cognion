"""`SQLAlchemyEstudianteEvaluacionesQueryRepository` contra PostgreSQL (US-9.4.3)."""

from __future__ import annotations

import uuid

from src.actividad_evaluativa.entities.ports.event_store_port import EventoParaAlmacenar
from src.actividad_evaluativa.frameworks.adapters.estudiante_evaluaciones_query_repository import (
    SQLAlchemyEstudianteEvaluacionesQueryRepository,
)
from src.actividad_evaluativa.frameworks.event_store.sqlalchemy_event_store import (
    SQLAlchemyEventStore,
)


async def _evento(session, aggregate_type: str, event_type: str, estudiante_id: uuid.UUID) -> None:
    await SQLAlchemyEventStore(session).append(
        aggregate_type,
        uuid.uuid4(),
        0,
        [EventoParaAlmacenar(event_type, {"estudiante_id": str(estudiante_id)})],
    )


class TestTieneEvaluacionesIniciadas:
    async def test_sin_eventos(self, session):
        repo = SQLAlchemyEstudianteEvaluacionesQueryRepository(session)

        assert await repo.tiene_evaluaciones_iniciadas(uuid.uuid4()) is False

    async def test_con_evaluacion_iniciada(self, session):
        estudiante_id = uuid.uuid4()
        await _evento(session, "Evaluacion", "EvaluacionIniciada", estudiante_id)

        repo = SQLAlchemyEstudianteEvaluacionesQueryRepository(session)
        assert await repo.tiene_evaluaciones_iniciadas(estudiante_id) is True

    async def test_ignora_otro_estudiante_otro_evento_y_otro_agregado(self, session):
        estudiante_id = uuid.uuid4()
        await _evento(session, "Evaluacion", "EvaluacionIniciada", uuid.uuid4())
        await _evento(session, "Evaluacion", "RespuestaRegistrada", estudiante_id)
        await _evento(session, "ParticipacionEnVivo", "EvaluacionIniciada", estudiante_id)

        repo = SQLAlchemyEstudianteEvaluacionesQueryRepository(session)
        assert await repo.tiene_evaluaciones_iniciadas(estudiante_id) is False
