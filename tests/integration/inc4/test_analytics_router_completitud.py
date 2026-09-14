"""Tests de integración de `GET /analytics/actividades/{id}/completitud` (US-ADJ-47, RF-23).

Escribe eventos reales de `ActividadEvaluativaPeriodoAbierto`/`Evaluacion` (tabla `events`) y
comisiones/estudiantes reales (Identidad), y ejercita el endpoint completo — router →
`AnalyticsCompletitudController` → use case → los 2 adapters — vía `AsyncClient`, mismos
escenarios que
`tests/features/inc5-adj/US-ADJ-47-completitud-por-actividad.feature`.
"""

from __future__ import annotations

import uuid
from datetime import UTC, datetime, timedelta
from uuid import uuid4

from httpx import ASGITransport, AsyncClient

from src.actividad_evaluativa.entities.ports.event_store_port import EventoParaAlmacenar
from src.actividad_evaluativa.frameworks.event_store.sqlalchemy_event_store import (
    SQLAlchemyEventStore,
)
from src.app import app
from src.identidad.entities.comision import Comision
from src.identidad.entities.usuario import Usuario
from src.identidad.frameworks.security.password_hasher import BcryptPasswordHasher
from src.identidad.interface_adapters.gateways.comision_repository import (
    SQLAlchemyComisionRepository,
)
from src.identidad.interface_adapters.gateways.usuario_repository import (
    SQLAlchemyUsuarioRepository,
)
from src.shared.entities.tipo_perfil import TipoPerfil
from src.shared.frameworks.security.jwt_pyjwt import PyJWTIssuer

AGGREGATE_TYPE_EVALUACION = "Evaluacion"
AGGREGATE_TYPE_ACTIVIDAD = "ActividadEvaluativaPeriodoAbierto"


async def _comision_con_estudiantes(session, materia_id, cantidad: int) -> tuple[uuid.UUID, list]:
    hasher = BcryptPasswordHasher()
    usuario_repo = SQLAlchemyUsuarioRepository(session)
    comision_repo = SQLAlchemyComisionRepository(session)

    admin = Usuario.crear(
        "Admin", f"admin.{uuid.uuid4()}@fiuner.edu.ar", hasher.hash("x"), TipoPerfil.ADMINISTRADOR
    )
    await usuario_repo.guardar(admin)
    comision = Comision.crear(materia_id, "lu 10-12", admin.id)
    await comision_repo.guardar(comision)

    estudiantes = []
    for _ in range(cantidad):
        estudiante = Usuario.crear_estudiante(
            "Estudiante", f"estudiante.{uuid.uuid4()}@fiuner.edu.ar", hasher.hash("x"), comision.id
        )
        await usuario_repo.guardar(estudiante)
        estudiantes.append(estudiante)
    return comision.id, estudiantes


async def _actividad_creada(
    store: SQLAlchemyEventStore, actividad_id, materia_id, comisiones_ids: frozenset | None = None
) -> None:
    ahora = datetime.now(UTC)
    await store.append(
        AGGREGATE_TYPE_ACTIVIDAD,
        actividad_id,
        0,
        [
            EventoParaAlmacenar(
                event_type="ActividadEvaluativaCreada",
                payload={
                    "actividad_id": str(actividad_id),
                    "materia_id": str(materia_id),
                    "fecha_apertura": (ahora - timedelta(days=1)).isoformat(),
                    "fecha_cierre": (ahora + timedelta(days=1)).isoformat(),
                    "cantidad_preguntas": 5,
                    "cantidad_intentos_permitidos": 1,
                    "titulo": "Actividad de prueba",
                    "comisiones_ids": [str(c) for c in (comisiones_ids or frozenset())],
                    "unidad_tematica": None,
                    "tema": None,
                    "ocurrido_en": ahora.isoformat(),
                },
            )
        ],
    )


async def _iniciar_evaluacion(
    store: SQLAlchemyEventStore, actividad_id, estudiante_id
) -> uuid.UUID:
    evaluacion_id = uuid4()
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
                    "ocurrido_en": datetime.now(UTC).isoformat(),
                    "preguntas_asignadas": [],
                },
            )
        ],
    )
    return evaluacion_id


async def _suspender(store: SQLAlchemyEventStore, evaluacion_id) -> None:
    await store.append(
        AGGREGATE_TYPE_EVALUACION,
        evaluacion_id,
        1,
        [
            EventoParaAlmacenar(
                event_type="EvaluacionSuspendida",
                payload={"evaluacion_id": str(evaluacion_id), "actor": "estudiante"},
            )
        ],
    )


async def _finalizar(store: SQLAlchemyEventStore, evaluacion_id) -> None:
    await store.append(
        AGGREGATE_TYPE_EVALUACION,
        evaluacion_id,
        1,
        [
            EventoParaAlmacenar(
                event_type="EvaluacionFinalizada",
                payload={"evaluacion_id": str(evaluacion_id), "actor": "estudiante"},
            )
        ],
    )


class TestAnalyticsRouterCompletitud:
    """Escenarios de `tests/features/inc5-adj/US-ADJ-47-completitud-por-actividad.feature`."""

    async def test_actividad_restringida_estados_mixtos(self, session, docente_headers):
        materia_id = uuid4()
        comision_id, estudiantes = await _comision_con_estudiantes(session, materia_id, 4)
        finalizo, en_curso, suspendio, nunca_inicio = estudiantes

        store = SQLAlchemyEventStore(session)
        actividad_id = uuid4()
        await _actividad_creada(store, actividad_id, materia_id, frozenset({comision_id}))

        evaluacion_finalizo = await _iniciar_evaluacion(store, actividad_id, finalizo.id)
        await _finalizar(store, evaluacion_finalizo)
        await _iniciar_evaluacion(store, actividad_id, en_curso.id)
        evaluacion_suspendio = await _iniciar_evaluacion(store, actividad_id, suspendio.id)
        await _suspender(store, evaluacion_suspendio)

        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.get(
                f"/analytics/actividades/{actividad_id}/completitud", headers=docente_headers
            )

        assert response.status_code == 200
        data = response.json()
        assert data["resumen"] == {
            "finalizadas": 1,
            "en_curso": 1,
            "suspendidas": 1,
            "sin_iniciar": 1,
        }
        estados_por_id = {fila["estudiante_id"]: fila["estado"] for fila in data["detalle"]}
        assert estados_por_id[str(nunca_inicio.id)] == "sin_iniciar"
        assert len(data["detalle"]) == 4

    async def test_actividad_sin_restriccion_de_comision(self, session, docente_headers):
        materia_id = uuid4()
        comision_1, estudiantes_1 = await _comision_con_estudiantes(session, materia_id, 1)
        comision_2, estudiantes_2 = await _comision_con_estudiantes(session, materia_id, 1)

        store = SQLAlchemyEventStore(session)
        actividad_id = uuid4()
        await _actividad_creada(store, actividad_id, materia_id)

        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.get(
                f"/analytics/actividades/{actividad_id}/completitud", headers=docente_headers
            )

        assert response.status_code == 200
        data = response.json()
        estudiante_ids = {fila["estudiante_id"] for fila in data["detalle"]}
        assert estudiante_ids == {str(estudiantes_1[0].id), str(estudiantes_2[0].id)}

    async def test_actividad_inexistente(self, docente_headers):
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.get(
                f"/analytics/actividades/{uuid4()}/completitud", headers=docente_headers
            )

        assert response.status_code == 404

    async def test_sin_autenticacion(self):
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.get(f"/analytics/actividades/{uuid4()}/completitud")

        assert response.status_code == 401

    async def test_rol_distinto_de_docente(self):
        jwt_vo = PyJWTIssuer().emitir(uuid4(), TipoPerfil.ESTUDIANTE)
        headers = {"Authorization": f"Bearer {jwt_vo.token}"}

        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.get(
                f"/analytics/actividades/{uuid4()}/completitud", headers=headers
            )

        assert response.status_code == 403
