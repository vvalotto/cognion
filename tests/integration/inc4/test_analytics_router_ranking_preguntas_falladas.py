"""Tests de integración de `GET /analytics/.../ranking-preguntas-falladas` (US-ADJ-46, RF-22).

Escribe eventos reales de `Evaluacion` (tabla `events`), una `Comision` real (Identidad) y
`PreguntaPlantilla` reales (Banco de Preguntas), y ejercita el endpoint completo — router →
`AnalyticsInformesController` → use case → los 3 adapters — vía `AsyncClient`, mismos
escenarios que `tests/features/inc5-adj/US-ADJ-46-ranking-preguntas-falladas.feature`.
"""

from __future__ import annotations

import uuid
from uuid import uuid4

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy import text

from src.actividad_evaluativa.entities.ports.event_store_port import EventoParaAlmacenar
from src.actividad_evaluativa.frameworks.event_store.sqlalchemy_event_store import (
    SQLAlchemyEventStore,
)
from src.app import app
from src.banco_preguntas.entities.banco import Banco
from src.banco_preguntas.entities.dificultad import Dificultad
from src.banco_preguntas.entities.importancia import Importancia
from src.banco_preguntas.entities.materia import Materia
from src.banco_preguntas.entities.metadatos_pregunta import MetadatosPregunta
from src.banco_preguntas.entities.opcion import Opcion
from src.banco_preguntas.entities.pregunta_plantilla import PreguntaPlantillaOpcionMultiple
from src.banco_preguntas.interface_adapters.gateways.banco_repository import (
    SQLAlchemyBancoRepository,
)
from src.banco_preguntas.interface_adapters.gateways.materia_repository import (
    SQLAlchemyMateriaRepository,
)
from src.banco_preguntas.interface_adapters.gateways.pregunta_repository import (
    SQLAlchemyPreguntaRepository,
)
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


async def _limpiar_tablas_banco_preguntas(session) -> None:
    await session.execute(text("DELETE FROM pregunta_plantilla"))
    await session.execute(text("DELETE FROM banco"))
    await session.execute(text("DELETE FROM materia"))
    await session.commit()


@pytest.fixture(autouse=True)
async def limpiar_tablas_banco_preguntas(session):
    await _limpiar_tablas_banco_preguntas(session)
    yield
    await _limpiar_tablas_banco_preguntas(session)


async def _pregunta_persistida(session, banco_id, unidad_tematica: str, tema: str) -> uuid.UUID:
    pregunta_repo = SQLAlchemyPreguntaRepository(session)
    pregunta = PreguntaPlantillaOpcionMultiple.crear(
        banco_id=banco_id,
        metadatos=MetadatosPregunta(
            texto=f"Pregunta {uuid.uuid4()}",
            unidad_tematica=unidad_tematica,
            tema=tema,
            dificultad=Dificultad.MEDIO,
            importancia=Importancia.ALTO,
        ),
        opciones=[Opcion(texto="A", es_correcta=True), Opcion(texto="B", es_correcta=False)],
    )
    await pregunta_repo.guardar(pregunta)
    return pregunta.id


async def _comision_con_estudiante(session, materia_id) -> tuple[uuid.UUID, Usuario]:
    hasher = BcryptPasswordHasher()
    usuario_repo = SQLAlchemyUsuarioRepository(session)
    comision_repo = SQLAlchemyComisionRepository(session)

    admin = Usuario.crear(
        "Admin", f"admin.{uuid.uuid4()}@fiuner.edu.ar", hasher.hash("x"), TipoPerfil.ADMINISTRADOR
    )
    await usuario_repo.guardar(admin)
    comision = Comision.crear(materia_id, "lu 10-12", admin.id)
    await comision_repo.guardar(comision)

    estudiante = Usuario.crear_estudiante(
        "Estudiante", f"estudiante.{uuid.uuid4()}@fiuner.edu.ar", hasher.hash("x"), comision.id
    )
    await usuario_repo.guardar(estudiante)
    return comision.id, estudiante


async def _actividad_creada(store: SQLAlchemyEventStore, actividad_id, materia_id) -> None:
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


async def _evaluacion_finalizada_con_respuesta(
    store: SQLAlchemyEventStore, actividad_id, estudiante_id, pregunta_id, es_correcta: bool
) -> None:
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
                },
            )
        ],
    )
    await store.append(
        AGGREGATE_TYPE_EVALUACION,
        evaluacion_id,
        1,
        [
            EventoParaAlmacenar(
                event_type="RespuestaRegistrada",
                payload={
                    "respuesta_id": str(uuid4()),
                    "evaluacion_id": str(evaluacion_id),
                    "pregunta_id": str(pregunta_id),
                    "numero_intento": 1,
                    "contenido": {},
                    "es_correcta": es_correcta,
                },
            )
        ],
    )
    await store.append(
        AGGREGATE_TYPE_EVALUACION,
        evaluacion_id,
        2,
        [
            EventoParaAlmacenar(
                event_type="EvaluacionFinalizada",
                payload={"evaluacion_id": str(evaluacion_id), "actor": "estudiante"},
            )
        ],
    )


class TestAnalyticsRouterRankingPreguntasFalladas:
    """Escenarios de `tests/features/inc5-adj/US-ADJ-46-ranking-preguntas-falladas.feature`."""

    async def test_materia_completa_ordenada_por_tasa_de_error(self, session, docente_headers):
        materia_repo = SQLAlchemyMateriaRepository(session)
        banco_repo = SQLAlchemyBancoRepository(session)
        materia = Materia.crear(f"Ingeniería de Software {uuid.uuid4()}")
        await materia_repo.guardar(materia)
        banco = Banco.crear(materia.id)
        await banco_repo.guardar(banco)

        pregunta_baja = await _pregunta_persistida(session, banco.id, "Unidad 1", "T1")
        pregunta_alta = await _pregunta_persistida(session, banco.id, "Unidad 1", "T2")
        _, estudiante = await _comision_con_estudiante(session, materia.id)

        store = SQLAlchemyEventStore(session)
        actividad_id = uuid4()
        await _actividad_creada(store, actividad_id, materia.id)
        await _evaluacion_finalizada_con_respuesta(
            store, actividad_id, estudiante.id, pregunta_baja, True
        )
        await _evaluacion_finalizada_con_respuesta(
            store, actividad_id, estudiante.id, pregunta_alta, False
        )

        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.get(
                f"/analytics/materias/{materia.id}/ranking-preguntas-falladas",
                headers=docente_headers,
            )

        assert response.status_code == 200
        data = response.json()
        assert len(data) == 2
        assert data[0]["pregunta_id"] == str(pregunta_alta)
        assert data[0]["tasa_error"] == 1.0
        assert data[0]["enunciado"]
        assert data[1]["pregunta_id"] == str(pregunta_baja)
        assert data[1]["tasa_error"] == 0.0

    async def test_acotado_a_una_comision(self, session, docente_headers):
        materia_repo = SQLAlchemyMateriaRepository(session)
        banco_repo = SQLAlchemyBancoRepository(session)
        materia = Materia.crear(f"Ingeniería de Software {uuid.uuid4()}")
        await materia_repo.guardar(materia)
        banco = Banco.crear(materia.id)
        await banco_repo.guardar(banco)
        pregunta_id = await _pregunta_persistida(session, banco.id, "Unidad 1", "T1")

        comision_1_id, estudiante_1 = await _comision_con_estudiante(session, materia.id)
        _, estudiante_2 = await _comision_con_estudiante(session, materia.id)

        store = SQLAlchemyEventStore(session)
        actividad_id = uuid4()
        await _actividad_creada(store, actividad_id, materia.id)
        await _evaluacion_finalizada_con_respuesta(
            store, actividad_id, estudiante_1.id, pregunta_id, False
        )
        await _evaluacion_finalizada_con_respuesta(
            store, actividad_id, estudiante_2.id, pregunta_id, True
        )

        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.get(
                f"/analytics/materias/{materia.id}/ranking-preguntas-falladas",
                params={"comision_id": str(comision_1_id)},
                headers=docente_headers,
            )

        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["cantidad_presentaciones"] == 1
        assert data[0]["cantidad_fallos"] == 1
        assert data[0]["tasa_error"] == 1.0

    async def test_materia_sin_preguntas_presentadas(self, docente_headers):
        materia_id = uuid4()

        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.get(
                f"/analytics/materias/{materia_id}/ranking-preguntas-falladas",
                headers=docente_headers,
            )

        assert response.status_code == 200
        assert response.json() == []

    async def test_comision_que_no_pertenece_a_la_materia(self, session, docente_headers):
        materia_repo = SQLAlchemyMateriaRepository(session)
        materia = Materia.crear(f"Ingeniería de Software {uuid.uuid4()}")
        await materia_repo.guardar(materia)
        otra_materia_id = uuid4()
        comision_de_otra_materia, _ = await _comision_con_estudiante(session, otra_materia_id)

        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.get(
                f"/analytics/materias/{materia.id}/ranking-preguntas-falladas",
                params={"comision_id": str(comision_de_otra_materia)},
                headers=docente_headers,
            )

        assert response.status_code == 422

    async def test_sin_autenticacion(self):
        materia_id = uuid4()

        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.get(
                f"/analytics/materias/{materia_id}/ranking-preguntas-falladas"
            )

        assert response.status_code == 401

    async def test_rol_distinto_de_docente(self):
        materia_id = uuid4()
        jwt_vo = PyJWTIssuer().emitir(uuid4(), TipoPerfil.ESTUDIANTE)
        headers = {"Authorization": f"Bearer {jwt_vo.token}"}

        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.get(
                f"/analytics/materias/{materia_id}/ranking-preguntas-falladas", headers=headers
            )

        assert response.status_code == 403
