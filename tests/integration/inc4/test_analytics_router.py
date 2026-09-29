"""Tests de integración de `GET /analytics/.../desempeno` (US-4.1.2, US-4.2.1).

Escribe eventos reales en la tabla `events` (mismo patrón que
`tests/integration/inc4/test_evaluacion_desempeno_consulta_port.py`, US-4.1.1) y ejercita el
endpoint completo — router → controller → use case → adapter — vía `AsyncClient`, mismos
escenarios que `tests/features/inc4/US-4.1.2-desempeno-estudiante.feature` y
`tests/features/inc4/US-4.2.1-desempeno-estudiante-elegido.feature`.
"""

from __future__ import annotations

import uuid
from uuid import uuid4

from httpx import ASGITransport, AsyncClient

from src.actividad_evaluativa.entities.ports.event_store_port import EventoParaAlmacenar
from src.actividad_evaluativa.frameworks.adapters.proyecciones_en_vivo_repository import (
    SQLAlchemyProyeccionesEnVivo,
)
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
from tests.integration.conftest import asignar_docente_a_materia

AGGREGATE_TYPE_EVALUACION = "Evaluacion"
AGGREGATE_TYPE_ACTIVIDAD = "ActividadEvaluativaPeriodoAbierto"


def _headers_estudiante(estudiante_id) -> dict[str, str]:
    jwt_vo = PyJWTIssuer().emitir(estudiante_id, TipoPerfil.ESTUDIANTE)
    return {"Authorization": f"Bearer {jwt_vo.token}"}


async def _crear_estudiante_real(session) -> Usuario:
    """Persiste un `Usuario` con rol Estudiante real — lo exige `EstudianteConsultaPort.existe`."""
    hasher = BcryptPasswordHasher()
    usuario_repo = SQLAlchemyUsuarioRepository(session)
    comision_repo = SQLAlchemyComisionRepository(session)

    admin = Usuario.crear(
        "Admin", f"admin.{uuid.uuid4()}@fiuner.edu.ar", hasher.hash("x"), TipoPerfil.ADMINISTRADOR
    )
    await usuario_repo.guardar(admin)
    comision = Comision.crear(uuid.uuid4(), "lu 10-12", admin.id)
    await comision_repo.guardar(comision)

    estudiante = Usuario.crear_estudiante(
        "Estudiante", f"estudiante.{uuid.uuid4()}@fiuner.edu.ar", hasher.hash("x"), comision.id
    )
    await usuario_repo.guardar(estudiante)
    return estudiante


AGGREGATE_TYPE_SESION_EN_VIVO = "ActividadEvaluativaEnVivo"
AGGREGATE_TYPE_PARTICIPACION_EN_VIVO = "ParticipacionEnVivo"


async def _crear_estudiante_de_materia(session, materia_id) -> tuple[Usuario, Comision]:
    """Igual que `_crear_estudiante_real`, pero con `materia_id` explícito (`US-ADJ-56`)."""
    hasher = BcryptPasswordHasher()
    usuario_repo = SQLAlchemyUsuarioRepository(session)
    comision_repo = SQLAlchemyComisionRepository(session)

    admin = Usuario.crear(
        "Admin", f"admin.{uuid.uuid4()}@fiuner.edu.ar", hasher.hash("x"), TipoPerfil.ADMINISTRADOR
    )
    await usuario_repo.guardar(admin)
    comision = Comision.crear(materia_id, "Lunes 14-16hs", admin.id)
    await comision_repo.guardar(comision)

    estudiante = Usuario.crear_estudiante(
        "Estudiante", f"estudiante.{uuid.uuid4()}@fiuner.edu.ar", hasher.hash("x"), comision.id
    )
    await usuario_repo.guardar(estudiante)
    return estudiante, comision


async def _crear_sesion_en_vivo(
    store: SQLAlchemyEventStore, sesion_id, comision_id, materia_id
) -> None:
    await store.append(
        AGGREGATE_TYPE_SESION_EN_VIVO,
        sesion_id,
        0,
        [
            EventoParaAlmacenar(
                event_type="SesionEnVivoCreada",
                payload={
                    "sesion_id": str(sesion_id),
                    "comision_id": str(comision_id),
                    "materia_id": str(materia_id),
                    "preguntas": [{"pregunta_id": str(uuid4()), "orden": 0}],
                    "tiempo_limite_por_pregunta_segundos": 20,
                    "unidad_tematica": None,
                    "tema": None,
                },
            )
        ],
    )


async def _finalizar_sesion_en_vivo(
    store: SQLAlchemyEventStore, sesion_id, expected_seq: int
) -> None:
    await store.append(
        AGGREGATE_TYPE_SESION_EN_VIVO,
        sesion_id,
        expected_seq,
        [
            EventoParaAlmacenar(
                event_type="SesionEnVivoFinalizada", payload={"sesion_id": str(sesion_id)}
            )
        ],
    )


async def _unir_y_responder_en_vivo(
    store: SQLAlchemyEventStore, session, sesion_id, estudiante_id, es_correcta: bool, puntaje: int
) -> None:
    """Une al estudiante, registra una respuesta y suma el puntaje en `ranking_por_sesion`."""
    participacion_id = uuid4()
    await store.append(
        AGGREGATE_TYPE_PARTICIPACION_EN_VIVO,
        participacion_id,
        0,
        [
            EventoParaAlmacenar(
                event_type="EstudianteUnido",
                payload={
                    "sesion_id": str(sesion_id),
                    "estudiante_id": str(estudiante_id),
                    "unido_en": "2026-01-01T00:00:00+00:00",
                },
            )
        ],
    )
    await store.append(
        AGGREGATE_TYPE_PARTICIPACION_EN_VIVO,
        participacion_id,
        1,
        [
            EventoParaAlmacenar(
                event_type="RespuestaEnVivoRegistrada",
                payload={
                    "pregunta_id": str(uuid4()),
                    "contenido": {"opcion_indice": 0},
                    "es_correcta": es_correcta,
                    "tiempo_respuesta_segundos": 4.2,
                    "puntaje": puntaje,
                },
            )
        ],
    )
    proyecciones = SQLAlchemyProyeccionesEnVivo(session)
    await proyecciones.inicializar_participante(sesion_id, estudiante_id)
    await proyecciones.registrar_respuesta(sesion_id, estudiante_id, uuid4(), "0", puntaje)
    await session.commit()


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


async def _finalizar_evaluacion(
    store: SQLAlchemyEventStore, evaluacion_id, expected_seq: int
) -> int:
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


class TestAnalyticsRouterSesionesEnVivo:
    """Sección "Sesiones en vivo" de `GET .../mi-desempeno` (`US-ADJ-56`, end-to-end real)."""

    async def test_mi_desempeno_incluye_la_sesion_en_vivo_finalizada_con_el_horario_real(
        self, session
    ):
        materia_id = uuid4()
        estudiante, comision = await _crear_estudiante_de_materia(session, materia_id)

        store = SQLAlchemyEventStore(session)
        sesion_id = uuid4()
        await _crear_sesion_en_vivo(store, sesion_id, comision.id, materia_id)
        await _unir_y_responder_en_vivo(store, session, sesion_id, estudiante.id, True, 850)
        await _finalizar_sesion_en_vivo(store, sesion_id, expected_seq=1)

        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.get(
                f"/analytics/materias/{materia_id}/mi-desempeno",
                headers=_headers_estudiante(estudiante.id),
            )

        assert response.status_code == 200
        data = response.json()
        assert len(data["sesiones_en_vivo"]) == 1
        fila = data["sesiones_en_vivo"][0]
        assert fila["sesion_id"] == str(sesion_id)
        assert fila["comision_horario"] == "Lunes 14-16hs"
        assert fila["cantidad_correctas"] == 1
        assert fila["puntaje_final"] == 850
        assert fila["posicion"] == 1
        assert fila["total_participantes"] == 1
        # El resumen de período abierto no se ve afectado por las sesiones en vivo.
        assert data["resumen"]["cantidad_evaluaciones"] == 0

    async def test_sin_sesiones_en_vivo_el_campo_viene_como_lista_vacia(self, session):
        estudiante_id, materia_id = uuid4(), uuid4()

        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.get(
                f"/analytics/materias/{materia_id}/mi-desempeno",
                headers=_headers_estudiante(estudiante_id),
            )

        assert response.status_code == 200
        assert response.json()["sesiones_en_vivo"] == []


class TestAnalyticsRouterDesempenoDeEstudiante:
    """Escenarios de `tests/features/inc4/US-4.2.1-desempeno-estudiante-elegido.feature`."""

    async def test_estudiante_con_evaluaciones_finalizadas(self, session, docente_headers):
        estudiante = await _crear_estudiante_real(session)
        store = SQLAlchemyEventStore(session)
        materia_id, actividad_id = uuid4(), uuid4()
        await asignar_docente_a_materia(str(materia_id), docente_headers)
        await _crear_actividad(store, actividad_id, materia_id)
        await _evaluacion_finalizada(store, actividad_id, estudiante.id, 8, 2)

        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.get(
                f"/analytics/materias/{materia_id}/estudiantes/{estudiante.id}/desempeno",
                headers=docente_headers,
            )

        assert response.status_code == 200
        data = response.json()
        assert len(data["evaluaciones"]) == 1
        assert data["resumen"] == {
            "total_correctas": 8,
            "total_incorrectas": 2,
            "porcentaje_acierto": 80,
            "cantidad_evaluaciones": 1,
        }

    async def test_estudiante_sin_evaluaciones_finalizadas(self, session, docente_headers):
        estudiante = await _crear_estudiante_real(session)
        materia_id = uuid4()
        await asignar_docente_a_materia(str(materia_id), docente_headers)

        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.get(
                f"/analytics/materias/{materia_id}/estudiantes/{estudiante.id}/desempeno",
                headers=docente_headers,
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

    async def test_estudiante_inexistente(self, docente_headers):
        materia_id, estudiante_id = uuid4(), uuid4()

        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.get(
                f"/analytics/materias/{materia_id}/estudiantes/{estudiante_id}/desempeno",
                headers=docente_headers,
            )

        assert response.status_code == 404

    async def test_sin_autenticacion(self):
        materia_id, estudiante_id = uuid4(), uuid4()

        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.get(
                f"/analytics/materias/{materia_id}/estudiantes/{estudiante_id}/desempeno"
            )

        assert response.status_code == 401

    async def test_rol_distinto_de_docente(self):
        materia_id, otro_estudiante_id = uuid4(), uuid4()
        headers = _headers_estudiante(uuid4())

        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.get(
                f"/analytics/materias/{materia_id}/estudiantes/{otro_estudiante_id}/desempeno",
                headers=headers,
            )

        assert response.status_code == 403
