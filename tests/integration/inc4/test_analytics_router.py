"""Tests de integración de `GET /analytics/materias/{materia_id}/mi-desempeno` (US-4.1.2).

Escribe eventos reales en la tabla `events` (mismo patrón que
`tests/integration/inc4/test_evaluacion_desempeno_consulta_port.py`, US-4.1.1) y ejercita el
endpoint completo — router → controller → use case → adapter — vía `AsyncClient`, mismos 5
escenarios que `tests/features/inc4/US-4.1.2-desempeno-estudiante.feature`.
"""

from __future__ import annotations

from uuid import uuid4

from httpx import ASGITransport, AsyncClient

from src.actividad_evaluativa.entities.ports.event_store_port import EventoParaAlmacenar
from src.actividad_evaluativa.frameworks.event_store.sqlalchemy_event_store import (
    SQLAlchemyEventStore,
)
from src.app import app
from src.shared.entities.tipo_perfil import TipoPerfil
from src.shared.frameworks.security.jwt_pyjwt import PyJWTIssuer

AGGREGATE_TYPE_EVALUACION = "Evaluacion"
AGGREGATE_TYPE_ACTIVIDAD = "ActividadEvaluativaPeriodoAbierto"


def _headers_estudiante(estudiante_id) -> dict[str, str]:
    jwt_vo = PyJWTIssuer().emitir(estudiante_id, TipoPerfil.ESTUDIANTE)
    return {"Authorization": f"Bearer {jwt_vo.token}"}


async def _crear_actividad(store: SQLAlchemyEventStore, actividad_id, materia_id) -> None:
    await store.append(
        AGGREGATE_TYPE_ACTIVIDAD,
        actividad_id,
        0,
        [
            EventoParaAlmacenar(
                event_type="ActividadEvaluativaCreada",
                payload={"actividad_id": str(actividad_id), "materia_id": str(materia_id)},
            )
        ],
    )


async def _iniciar_evaluacion(
    store: SQLAlchemyEventStore, evaluacion_id, actividad_id, estudiante_id
) -> int:
    await store.append(
        AGGREGATE_TYPE_EVALUACION,
        evaluacion_id,
        0,
        [
            EventoParaAlmacenar(
                event_type="EvaluacionIniciada",
                payload={
                    "evaluacion_id": str(evaluacion_id),
                    "actividad_id": str(actividad_id),
                    "estudiante_id": str(estudiante_id),
                },
            )
        ],
    )
    return 1


async def _registrar_respuesta(
    store: SQLAlchemyEventStore,
    evaluacion_id,
    expected_seq: int,
    es_correcta: bool,
) -> int:
    await store.append(
        AGGREGATE_TYPE_EVALUACION,
        evaluacion_id,
        expected_seq,
        [
            EventoParaAlmacenar(
                event_type="RespuestaRegistrada",
                payload={
                    "respuesta_id": str(uuid4()),
                    "evaluacion_id": str(evaluacion_id),
                    "pregunta_id": str(uuid4()),
                    "numero_intento": 1,
                    "contenido": {},
                    "es_correcta": es_correcta,
                },
            )
        ],
    )
    return expected_seq + 1


async def _finalizar_evaluacion(store: SQLAlchemyEventStore, evaluacion_id, expected_seq: int) -> int:
    await store.append(
        AGGREGATE_TYPE_EVALUACION,
        evaluacion_id,
        expected_seq,
        [
            EventoParaAlmacenar(
                event_type="EvaluacionFinalizada",
                payload={"evaluacion_id": str(evaluacion_id), "actor": "estudiante"},
            )
        ],
    )
    return expected_seq + 1


async def _evaluacion_finalizada(
    store: SQLAlchemyEventStore, actividad_id, estudiante_id, correctas: int, incorrectas: int
) -> None:
    evaluacion_id = uuid4()
    seq = await _iniciar_evaluacion(store, evaluacion_id, actividad_id, estudiante_id)
    for _ in range(correctas):
        seq = await _registrar_respuesta(store, evaluacion_id, seq, True)
    for _ in range(incorrectas):
        seq = await _registrar_respuesta(store, evaluacion_id, seq, False)
    await _finalizar_evaluacion(store, evaluacion_id, seq)


class TestAnalyticsRouterMiDesempeno:
    """Escenarios de `tests/features/inc4/US-4.1.2-desempeno-estudiante.feature`."""

    async def test_desempeno_con_evaluaciones_finalizadas(self, session):
        store = SQLAlchemyEventStore(session)
        estudiante_id, materia_id, actividad_id = uuid4(), uuid4(), uuid4()
        await _crear_actividad(store, actividad_id, materia_id)
        await _evaluacion_finalizada(store, actividad_id, estudiante_id, 8, 2)
        await _evaluacion_finalizada(store, actividad_id, estudiante_id, 5, 3)

        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.get(
                f"/analytics/materias/{materia_id}/mi-desempeno",
                headers=_headers_estudiante(estudiante_id),
            )

        assert response.status_code == 200
        data = response.json()
        assert len(data["evaluaciones"]) == 2
        assert data["resumen"] == {
            "total_correctas": 13,
            "total_incorrectas": 5,
            "porcentaje_acierto": 72,
            "cantidad_evaluaciones": 2,
        }

    async def test_materia_sin_evaluaciones_finalizadas(self, session):
        estudiante_id, materia_id = uuid4(), uuid4()

        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.get(
                f"/analytics/materias/{materia_id}/mi-desempeno",
                headers=_headers_estudiante(estudiante_id),
            )

        assert response.status_code == 200
        data = response.json()
        assert data["evaluaciones"] == []
        assert data["resumen"] == {
            "total_correctas": 0,
            "total_incorrectas": 0,
            "porcentaje_acierto": 0,
            "cantidad_evaluaciones": 0,
        }

    async def test_sin_autenticacion(self):
        materia_id = uuid4()

        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.get(f"/analytics/materias/{materia_id}/mi-desempeno")

        assert response.status_code == 401

    async def test_rol_distinto_de_estudiante(self, docente_headers):
        materia_id = uuid4()

        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.get(
                f"/analytics/materias/{materia_id}/mi-desempeno", headers=docente_headers
            )

        assert response.status_code == 403

    async def test_estudiante_solo_ve_su_propio_desempeno(self, session):
        store = SQLAlchemyEventStore(session)
        estudiante_a, estudiante_b = uuid4(), uuid4()
        materia_id, actividad_id = uuid4(), uuid4()
        await _crear_actividad(store, actividad_id, materia_id)
        await _evaluacion_finalizada(store, actividad_id, estudiante_b, 9, 1)

        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.get(
                f"/analytics/materias/{materia_id}/mi-desempeno",
                headers=_headers_estudiante(estudiante_a),
            )

        assert response.status_code == 200
        data = response.json()
        assert data["evaluaciones"] == []
        assert data["resumen"]["cantidad_evaluaciones"] == 0
