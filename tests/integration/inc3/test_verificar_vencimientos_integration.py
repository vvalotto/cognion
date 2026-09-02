import uuid
from datetime import UTC, datetime, timedelta

from httpx import ASGITransport, AsyncClient
from sqlalchemy import text

from src.actividad_evaluativa.frameworks.dependencies import (
    build_verificar_vencimientos_use_case,
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


def _headers_para(usuario: Usuario) -> dict[str, str]:
    jwt_vo = PyJWTIssuer().emitir(usuario.id, usuario.tipo_perfil)
    return {"Authorization": f"Bearer {jwt_vo.token}"}


async def _crear_estudiante(session) -> dict[str, str]:
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
    return _headers_para(estudiante)


async def _crear_materia(client: AsyncClient, headers: dict) -> tuple[str, str]:
    nombre = f"Ingeniería de Software {uuid.uuid4()}"
    creada = await client.post("/materias", json={"nombre": nombre}, headers=headers)
    return creada.json()["id"], creada.json()["banco_id"]


async def _cargar_verdadero_falso(client: AsyncClient, headers: dict, banco_id: str) -> None:
    await client.post(
        "/preguntas/verdadero-falso",
        json={
            "banco_id": banco_id,
            "texto": f"Pregunta VF {uuid.uuid4()}",
            "respuesta_correcta": True,
            "unidad_tematica": "Unidad 1",
            "tema": "Tema",
            "dificultad": "medio",
            "importancia": "alto",
        },
        headers=headers,
    )


async def _crear_actividad_vigente(client: AsyncClient, docente_headers: dict) -> str:
    materia_id, banco_id = await _crear_materia(client, docente_headers)
    await _cargar_verdadero_falso(client, docente_headers, banco_id)
    apertura = datetime.now(UTC) - timedelta(days=1)
    cierre = apertura + timedelta(days=7)
    response = await client.post(
        "/actividades",
        json={
            "materia_id": materia_id,
            "fecha_apertura": apertura.isoformat(),
            "fecha_cierre": cierre.isoformat(),
            "cantidad_preguntas": 1,
            "cantidad_intentos_permitidos": 1,
        },
        headers=docente_headers,
    )
    return response.json()["id"]


async def _iniciar_evaluacion(client: AsyncClient, headers: dict, actividad_id: str) -> str:
    response = await client.post(
        "/evaluaciones", json={"actividad_id": actividad_id}, headers=headers
    )
    return response.json()["id"]


async def _backdatear_ultima_actividad(session, evaluacion_id: str, momento: datetime) -> None:
    """Simula inactividad prolongada retrocediendo `occurred_at` de `EvaluacionIniciada`."""
    await session.execute(
        text(
            "UPDATE events SET occurred_at = :momento "
            "WHERE aggregate_type = 'Evaluacion' AND aggregate_id = :evaluacion_id "
            "AND event_type = 'EvaluacionIniciada'"
        ),
        {"momento": momento, "evaluacion_id": uuid.UUID(evaluacion_id)},
    )
    await session.commit()


async def _backdatear_fecha_cierre(
    session, actividad_id: str, nueva_fecha_cierre: datetime
) -> None:
    """Simula que el período ya venció, sin pasar por `US-3.3.1` (todavía no implementada)."""
    await session.execute(
        text(
            "UPDATE events SET payload = jsonb_set(payload, '{fecha_cierre}', to_jsonb(CAST(:fecha AS text))) "
            "WHERE aggregate_type = 'ActividadEvaluativaPeriodoAbierto' "
            "AND aggregate_id = :actividad_id"
        ),
        {"fecha": nueva_fecha_cierre.isoformat(), "actividad_id": uuid.UUID(actividad_id)},
    )
    await session.commit()


class TestVerificarVencimientosIntegration:
    """Escenarios de `tests/features/inc3/US-3.2.4-verificador-vencimientos.feature`."""

    async def test_regla_1_suspende_evaluacion_inactiva(self, session, docente_headers):
        estudiante_headers = await _crear_estudiante(session)
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            actividad_id = await _crear_actividad_vigente(client, docente_headers)
            evaluacion_id = await _iniciar_evaluacion(client, estudiante_headers, actividad_id)

        await _backdatear_ultima_actividad(
            session, evaluacion_id, datetime.now(UTC) - timedelta(minutes=30)
        )

        use_case = build_verificar_vencimientos_use_case(session)
        resultado = await use_case.execute()

        assert resultado.suspendidas == 1
        store = SQLAlchemyEventStore(session)
        stream = await store.load("Evaluacion", uuid.UUID(evaluacion_id))
        assert stream[-1].event_type == "EvaluacionSuspendida"
        assert stream[-1].payload["actor"] == "sistema"

    async def test_regla_1_no_afecta_evaluacion_con_actividad_reciente(
        self, session, docente_headers
    ):
        estudiante_headers = await _crear_estudiante(session)
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            actividad_id = await _crear_actividad_vigente(client, docente_headers)
            evaluacion_id = await _iniciar_evaluacion(client, estudiante_headers, actividad_id)

        use_case = build_verificar_vencimientos_use_case(session)
        resultado = await use_case.execute()

        assert resultado.suspendidas == 0
        store = SQLAlchemyEventStore(session)
        stream = await store.load("Evaluacion", uuid.UUID(evaluacion_id))
        assert len(stream) == 1

    async def test_regla_2_finaliza_evaluacion_de_actividad_vencida(self, session, docente_headers):
        estudiante_headers = await _crear_estudiante(session)
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            actividad_id = await _crear_actividad_vigente(client, docente_headers)
            evaluacion_id = await _iniciar_evaluacion(client, estudiante_headers, actividad_id)

        await _backdatear_fecha_cierre(session, actividad_id, datetime.now(UTC) - timedelta(days=1))

        use_case = build_verificar_vencimientos_use_case(session)
        resultado = await use_case.execute()

        assert resultado.finalizadas == 1
        store = SQLAlchemyEventStore(session)
        stream = await store.load("Evaluacion", uuid.UUID(evaluacion_id))
        assert stream[-1].event_type == "EvaluacionFinalizada"
        assert stream[-1].payload["actor"] == "sistema"

    async def test_idempotencia_segunda_corrida_es_no_op(self, session, docente_headers):
        estudiante_headers = await _crear_estudiante(session)
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            actividad_id = await _crear_actividad_vigente(client, docente_headers)
            evaluacion_id = await _iniciar_evaluacion(client, estudiante_headers, actividad_id)

        await _backdatear_fecha_cierre(session, actividad_id, datetime.now(UTC) - timedelta(days=1))

        use_case = build_verificar_vencimientos_use_case(session)
        primera = await use_case.execute()
        assert primera.finalizadas == 1

        segunda = await use_case.execute()

        assert segunda.finalizadas == 0
        store = SQLAlchemyEventStore(session)
        stream = await store.load("Evaluacion", uuid.UUID(evaluacion_id))
        assert len(stream) == 2
