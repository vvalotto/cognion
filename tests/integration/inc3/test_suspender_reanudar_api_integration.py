import asyncio
import uuid
from datetime import UTC, datetime, timedelta

from httpx import ASGITransport, AsyncClient

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


async def _crear_estudiante(session) -> tuple[Usuario, dict[str, str]]:
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
    return estudiante, _headers_para(estudiante)


async def _crear_materia(client: AsyncClient, headers: dict) -> tuple[str, str]:
    nombre = f"Ingeniería de Software {uuid.uuid4()}"
    creada = await client.post("/materias", json={"nombre": nombre}, headers=headers)
    return creada.json()["id"], creada.json()["banco_id"]


async def _cargar_verdadero_falso(
    client: AsyncClient, headers: dict, banco_id: str, respuesta_correcta: bool
) -> str:
    respuesta = await client.post(
        "/preguntas/verdadero-falso",
        json={
            "banco_id": banco_id,
            "texto": f"Pregunta VF {uuid.uuid4()}",
            "respuesta_correcta": respuesta_correcta,
            "unidad_tematica": "Unidad 1",
            "tema": "Tema",
            "dificultad": "medio",
            "importancia": "alto",
        },
        headers=headers,
    )
    return respuesta.json()["id"]


async def _crear_actividad(
    client: AsyncClient,
    docente_headers: dict,
    materia_id: str,
    apertura: datetime,
    cierre: datetime,
) -> str:
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


async def _iniciar_evaluacion(client: AsyncClient, headers: dict, actividad_id: str) -> dict:
    response = await client.post(
        "/evaluaciones", json={"actividad_id": actividad_id}, headers=headers
    )
    return response.json()


async def _preparar_evaluacion_en_curso(
    client: AsyncClient, docente_headers: dict, estudiante_headers: dict, session
) -> dict:
    materia_id, banco_id = await _crear_materia(client, docente_headers)
    await _cargar_verdadero_falso(client, docente_headers, banco_id, True)
    apertura = datetime.now(UTC) - timedelta(days=1)
    cierre = apertura + timedelta(days=7)
    actividad_id = await _crear_actividad(client, docente_headers, materia_id, apertura, cierre)
    return await _iniciar_evaluacion(client, estudiante_headers, actividad_id)


class TestSuspenderReanudarAPIIntegration:
    """Escenarios de `tests/features/inc3/US-3.2.2-suspender-reanudar-evaluacion.feature`."""

    async def test_suspende_una_evaluacion_en_curso(self, session, docente_headers):
        estudiante, estudiante_headers = await _crear_estudiante(session)
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            evaluacion = await _preparar_evaluacion_en_curso(
                client, docente_headers, estudiante_headers, session
            )

            response = await client.post(
                f"/evaluaciones/{evaluacion['id']}/suspender", headers=estudiante_headers
            )

        assert response.status_code == 200
        assert response.json()["estado"] == "Suspendida"
        store = SQLAlchemyEventStore(session)
        stream = await store.load("Evaluacion", uuid.UUID(evaluacion["id"]))
        assert stream[-1].event_type == "EvaluacionSuspendida"
        assert stream[-1].payload["actor"] == "estudiante"

    async def test_reanuda_una_evaluacion_suspendida(self, session, docente_headers):
        estudiante, estudiante_headers = await _crear_estudiante(session)
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            evaluacion = await _preparar_evaluacion_en_curso(
                client, docente_headers, estudiante_headers, session
            )
            await client.post(
                f"/evaluaciones/{evaluacion['id']}/suspender", headers=estudiante_headers
            )

            response = await client.post(
                f"/evaluaciones/{evaluacion['id']}/reanudar", headers=estudiante_headers
            )

        assert response.status_code == 200
        assert response.json()["estado"] == "EnCurso"
        store = SQLAlchemyEventStore(session)
        stream = await store.load("Evaluacion", uuid.UUID(evaluacion["id"]))
        assert stream[-1].event_type == "EvaluacionReanudada"

    async def test_reanudar_habilita_volver_a_registrar_respuestas(
        self, session, docente_headers
    ):
        estudiante, estudiante_headers = await _crear_estudiante(session)
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            evaluacion = await _preparar_evaluacion_en_curso(
                client, docente_headers, estudiante_headers, session
            )
            pregunta_id = evaluacion["preguntas_asignadas"][0]["pregunta_id"]
            await client.post(
                f"/evaluaciones/{evaluacion['id']}/suspender", headers=estudiante_headers
            )
            await client.post(
                f"/evaluaciones/{evaluacion['id']}/reanudar", headers=estudiante_headers
            )

            response = await client.post(
                f"/evaluaciones/{evaluacion['id']}/respuestas",
                json={"pregunta_id": pregunta_id, "contenido": {"valor": True}},
                headers=estudiante_headers,
            )

        assert response.status_code == 201

    async def test_rechaza_registrar_respuesta_sobre_evaluacion_suspendida(
        self, session, docente_headers
    ):
        estudiante, estudiante_headers = await _crear_estudiante(session)
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            evaluacion = await _preparar_evaluacion_en_curso(
                client, docente_headers, estudiante_headers, session
            )
            pregunta_id = evaluacion["preguntas_asignadas"][0]["pregunta_id"]
            await client.post(
                f"/evaluaciones/{evaluacion['id']}/suspender", headers=estudiante_headers
            )

            response = await client.post(
                f"/evaluaciones/{evaluacion['id']}/respuestas",
                json={"pregunta_id": pregunta_id, "contenido": {"valor": True}},
                headers=estudiante_headers,
            )

        assert response.status_code == 422

    async def test_rechazo_al_suspender_una_evaluacion_ya_suspendida(
        self, session, docente_headers
    ):
        estudiante, estudiante_headers = await _crear_estudiante(session)
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            evaluacion = await _preparar_evaluacion_en_curso(
                client, docente_headers, estudiante_headers, session
            )
            await client.post(
                f"/evaluaciones/{evaluacion['id']}/suspender", headers=estudiante_headers
            )

            response = await client.post(
                f"/evaluaciones/{evaluacion['id']}/suspender", headers=estudiante_headers
            )

        assert response.status_code == 422

    async def test_rechazo_al_reanudar_una_evaluacion_en_curso(self, session, docente_headers):
        estudiante, estudiante_headers = await _crear_estudiante(session)
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            evaluacion = await _preparar_evaluacion_en_curso(
                client, docente_headers, estudiante_headers, session
            )

            response = await client.post(
                f"/evaluaciones/{evaluacion['id']}/reanudar", headers=estudiante_headers
            )

        assert response.status_code == 422

    async def test_rechazo_al_reanudar_fuera_del_periodo_vigente(self, session, docente_headers):
        estudiante, estudiante_headers = await _crear_estudiante(session)
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            materia_id, banco_id = await _crear_materia(client, docente_headers)
            await _cargar_verdadero_falso(client, docente_headers, banco_id, True)
            apertura = datetime.now(UTC) - timedelta(days=1)
            cierre = datetime.now(UTC) + timedelta(seconds=1)
            actividad_id = await _crear_actividad(
                client, docente_headers, materia_id, apertura, cierre
            )
            evaluacion = await _iniciar_evaluacion(client, estudiante_headers, actividad_id)
            await client.post(
                f"/evaluaciones/{evaluacion['id']}/suspender", headers=estudiante_headers
            )
            await asyncio.sleep(1.2)

            response = await client.post(
                f"/evaluaciones/{evaluacion['id']}/reanudar", headers=estudiante_headers
            )

        assert response.status_code == 422

    async def test_suspender_no_valida_periodo_vigente(self, session, docente_headers):
        estudiante, estudiante_headers = await _crear_estudiante(session)
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            materia_id, banco_id = await _crear_materia(client, docente_headers)
            await _cargar_verdadero_falso(client, docente_headers, banco_id, True)
            apertura = datetime.now(UTC) - timedelta(days=1)
            cierre = apertura + timedelta(days=2)
            actividad_id = await _crear_actividad(client, docente_headers, materia_id, apertura, cierre)
            evaluacion = await _iniciar_evaluacion(client, estudiante_headers, actividad_id)

            response = await client.post(
                f"/evaluaciones/{evaluacion['id']}/suspender", headers=estudiante_headers
            )

        assert response.status_code == 200
        assert response.json()["estado"] == "Suspendida"

    async def test_rechazo_por_evaluacion_inexistente(self, session):
        _estudiante, estudiante_headers = await _crear_estudiante(session)
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.post(
                f"/evaluaciones/{uuid.uuid4()}/suspender", headers=estudiante_headers
            )

        assert response.status_code == 404

    async def test_rechazo_sin_autenticacion(self):
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.post(f"/evaluaciones/{uuid.uuid4()}/suspender")

        assert response.status_code == 401

    async def test_rechazo_con_rol_insuficiente(self, docente_headers):
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.post(
                f"/evaluaciones/{uuid.uuid4()}/suspender", headers=docente_headers
            )

        assert response.status_code == 403
