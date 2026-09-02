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
    client: AsyncClient, headers: dict, banco_id: str, respuesta_correcta: bool, cantidad: int = 1
) -> list[str]:
    ids = []
    for i in range(cantidad):
        respuesta = await client.post(
            "/preguntas/verdadero-falso",
            json={
                "banco_id": banco_id,
                "texto": f"Pregunta VF {i} {uuid.uuid4()}",
                "respuesta_correcta": respuesta_correcta,
                "unidad_tematica": "Unidad 1",
                "tema": "Tema",
                "dificultad": "medio",
                "importancia": "alto",
            },
            headers=headers,
        )
        ids.append(respuesta.json()["id"])
    return ids


async def _cargar_opcion_multiple(client: AsyncClient, headers: dict, banco_id: str) -> str:
    respuesta = await client.post(
        "/preguntas/opcion-multiple",
        json={
            "banco_id": banco_id,
            "texto": f"Pregunta OM {uuid.uuid4()}",
            "opciones": [
                {"texto": "Incorrecta", "es_correcta": False},
                {"texto": "Correcta", "es_correcta": True},
            ],
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
    cantidad_preguntas: int,
    apertura: datetime,
    cierre: datetime,
    cantidad_intentos_permitidos: int = 1,
) -> str:
    response = await client.post(
        "/actividades",
        json={
            "materia_id": materia_id,
            "fecha_apertura": apertura.isoformat(),
            "fecha_cierre": cierre.isoformat(),
            "cantidad_preguntas": cantidad_preguntas,
            "cantidad_intentos_permitidos": cantidad_intentos_permitidos,
        },
        headers=docente_headers,
    )
    return response.json()["id"]


async def _iniciar_evaluacion(client: AsyncClient, headers: dict, actividad_id: str) -> dict:
    response = await client.post(
        "/evaluaciones", json={"actividad_id": actividad_id}, headers=headers
    )
    return response.json()


class TestRegistrarRespuestaAPIIntegration:
    """Escenarios de `tests/features/inc3/US-3.2.1-registrar-respuesta.feature`."""

    async def test_confirma_respuesta_valida_verdadero_falso(self, session, docente_headers):
        estudiante, estudiante_headers = await _crear_estudiante(session)
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            materia_id, banco_id = await _crear_materia(client, docente_headers)
            await _cargar_verdadero_falso(client, docente_headers, banco_id, True)
            apertura = datetime.now(UTC) - timedelta(days=1)
            cierre = apertura + timedelta(days=7)
            actividad_id = await _crear_actividad(
                client, docente_headers, materia_id, 1, apertura, cierre
            )
            evaluacion = await _iniciar_evaluacion(client, estudiante_headers, actividad_id)
            pregunta_id = evaluacion["preguntas_asignadas"][0]["pregunta_id"]

            response = await client.post(
                f"/evaluaciones/{evaluacion['id']}/respuestas",
                json={"pregunta_id": pregunta_id, "contenido": {"valor": True}},
                headers=estudiante_headers,
            )

        assert response.status_code == 201
        data = response.json()
        assert data["pregunta_id"] == pregunta_id
        assert data["numero_intento"] == 1
        assert "es_correcta" not in data
        assert "contenido" not in data

        store = SQLAlchemyEventStore(session)
        stream = await store.load("Evaluacion", uuid.UUID(evaluacion["id"]))
        assert len(stream) == 2
        assert stream[1].event_type == "RespuestaRegistrada"
        assert stream[1].payload["es_correcta"] is True

    async def test_calcula_correccion_para_opcion_multiple(self, session, docente_headers):
        estudiante, estudiante_headers = await _crear_estudiante(session)
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            materia_id, banco_id = await _crear_materia(client, docente_headers)
            await _cargar_opcion_multiple(client, docente_headers, banco_id)
            apertura = datetime.now(UTC) - timedelta(days=1)
            cierre = apertura + timedelta(days=7)
            actividad_id = await _crear_actividad(
                client, docente_headers, materia_id, 1, apertura, cierre
            )
            evaluacion = await _iniciar_evaluacion(client, estudiante_headers, actividad_id)
            pregunta_id = evaluacion["preguntas_asignadas"][0]["pregunta_id"]

            await client.post(
                f"/evaluaciones/{evaluacion['id']}/respuestas",
                json={"pregunta_id": pregunta_id, "contenido": {"opcion_indice": 1}},
                headers=estudiante_headers,
            )

        store = SQLAlchemyEventStore(session)
        stream = await store.load("Evaluacion", uuid.UUID(evaluacion["id"]))
        assert stream[1].payload["es_correcta"] is True

    async def test_segundo_intento_incrementa_numero_intento(self, session, docente_headers):
        estudiante, estudiante_headers = await _crear_estudiante(session)
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            materia_id, banco_id = await _crear_materia(client, docente_headers)
            await _cargar_verdadero_falso(client, docente_headers, banco_id, True)
            apertura = datetime.now(UTC) - timedelta(days=1)
            cierre = apertura + timedelta(days=7)
            actividad_id = await _crear_actividad(
                client,
                docente_headers,
                materia_id,
                1,
                apertura,
                cierre,
                cantidad_intentos_permitidos=2,
            )
            evaluacion = await _iniciar_evaluacion(client, estudiante_headers, actividad_id)
            pregunta_id = evaluacion["preguntas_asignadas"][0]["pregunta_id"]
            await client.post(
                f"/evaluaciones/{evaluacion['id']}/respuestas",
                json={"pregunta_id": pregunta_id, "contenido": {"valor": True}},
                headers=estudiante_headers,
            )

            segunda = await client.post(
                f"/evaluaciones/{evaluacion['id']}/respuestas",
                json={"pregunta_id": pregunta_id, "contenido": {"valor": False}},
                headers=estudiante_headers,
            )

        assert segunda.status_code == 201
        assert segunda.json()["numero_intento"] == 2

    async def test_rechazo_por_intentos_agotados(self, session, docente_headers):
        estudiante, estudiante_headers = await _crear_estudiante(session)
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            materia_id, banco_id = await _crear_materia(client, docente_headers)
            await _cargar_verdadero_falso(client, docente_headers, banco_id, True)
            apertura = datetime.now(UTC) - timedelta(days=1)
            cierre = apertura + timedelta(days=7)
            actividad_id = await _crear_actividad(
                client, docente_headers, materia_id, 1, apertura, cierre
            )
            evaluacion = await _iniciar_evaluacion(client, estudiante_headers, actividad_id)
            pregunta_id = evaluacion["preguntas_asignadas"][0]["pregunta_id"]
            await client.post(
                f"/evaluaciones/{evaluacion['id']}/respuestas",
                json={"pregunta_id": pregunta_id, "contenido": {"valor": True}},
                headers=estudiante_headers,
            )

            response = await client.post(
                f"/evaluaciones/{evaluacion['id']}/respuestas",
                json={"pregunta_id": pregunta_id, "contenido": {"valor": False}},
                headers=estudiante_headers,
            )

        assert response.status_code == 422

    async def test_rechazo_por_pregunta_no_asignada(self, session, docente_headers):
        estudiante, estudiante_headers = await _crear_estudiante(session)
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            materia_id, banco_id = await _crear_materia(client, docente_headers)
            await _cargar_verdadero_falso(client, docente_headers, banco_id, True, cantidad=5)
            apertura = datetime.now(UTC) - timedelta(days=1)
            cierre = apertura + timedelta(days=7)
            actividad_id = await _crear_actividad(
                client, docente_headers, materia_id, 1, apertura, cierre
            )
            evaluacion = await _iniciar_evaluacion(client, estudiante_headers, actividad_id)

            response = await client.post(
                f"/evaluaciones/{evaluacion['id']}/respuestas",
                json={"pregunta_id": str(uuid.uuid4()), "contenido": {"valor": True}},
                headers=estudiante_headers,
            )

        assert response.status_code == 404

    async def test_rechazo_por_evaluacion_inexistente(self, session):
        _estudiante, estudiante_headers = await _crear_estudiante(session)
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.post(
                f"/evaluaciones/{uuid.uuid4()}/respuestas",
                json={"pregunta_id": str(uuid.uuid4()), "contenido": {"valor": True}},
                headers=estudiante_headers,
            )

        assert response.status_code == 404

    async def test_rechazo_sin_autenticacion(self):
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.post(
                f"/evaluaciones/{uuid.uuid4()}/respuestas",
                json={"pregunta_id": str(uuid.uuid4()), "contenido": {"valor": True}},
            )

        assert response.status_code == 401

    async def test_rechazo_con_rol_insuficiente(self, docente_headers):
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.post(
                f"/evaluaciones/{uuid.uuid4()}/respuestas",
                json={"pregunta_id": str(uuid.uuid4()), "contenido": {"valor": True}},
                headers=docente_headers,
            )

        assert response.status_code == 403
