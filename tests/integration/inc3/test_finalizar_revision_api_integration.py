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


async def _actividad_vigente(client, docente_headers, cantidad_preguntas: int = 1) -> tuple[str, str]:
    """Crea materia + banco con `cantidad_preguntas` VF (respuesta correcta True) + actividad.

    Carga las preguntas **antes** de crear la actividad — INV-AE-01 exige que
    `cantidad_preguntas` no supere las preguntas activas disponibles al momento de crearla.
    """
    materia_id, banco_id = await _crear_materia(client, docente_headers)
    for _ in range(cantidad_preguntas):
        await _cargar_verdadero_falso(client, docente_headers, banco_id, True)
    apertura = datetime.now(UTC) - timedelta(days=1)
    cierre = apertura + timedelta(days=7)
    actividad_id = await _crear_actividad(
        client, docente_headers, materia_id, cantidad_preguntas, apertura, cierre
    )
    return actividad_id, banco_id


class TestFinalizarAPIIntegration:
    """Escenarios de finalización de
    `tests/features/inc3/US-3.2.3-finalizar-evaluacion-revision.feature`."""

    async def test_finaliza_una_evaluacion_en_curso(self, session, docente_headers):
        estudiante, estudiante_headers = await _crear_estudiante(session)
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            actividad_id, banco_id = await _actividad_vigente(client, docente_headers)
            evaluacion = await _iniciar_evaluacion(client, estudiante_headers, actividad_id)

            response = await client.post(
                f"/evaluaciones/{evaluacion['id']}/finalizar", headers=estudiante_headers
            )

        assert response.status_code == 200
        assert response.json()["estado"] == "Finalizada"
        store = SQLAlchemyEventStore(session)
        stream = await store.load("Evaluacion", uuid.UUID(evaluacion["id"]))
        assert stream[-1].event_type == "EvaluacionFinalizada"
        assert stream[-1].payload["actor"] == "estudiante"

    async def test_finaliza_una_evaluacion_suspendida(self, session, docente_headers):
        estudiante, estudiante_headers = await _crear_estudiante(session)
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            actividad_id, banco_id = await _actividad_vigente(client, docente_headers)
            evaluacion = await _iniciar_evaluacion(client, estudiante_headers, actividad_id)
            await client.post(
                f"/evaluaciones/{evaluacion['id']}/suspender", headers=estudiante_headers
            )

            response = await client.post(
                f"/evaluaciones/{evaluacion['id']}/finalizar", headers=estudiante_headers
            )

        assert response.status_code == 200
        assert response.json()["estado"] == "Finalizada"

    async def test_rechazo_al_finalizar_una_evaluacion_ya_finalizada(
        self, session, docente_headers
    ):
        estudiante, estudiante_headers = await _crear_estudiante(session)
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            actividad_id, banco_id = await _actividad_vigente(client, docente_headers)
            evaluacion = await _iniciar_evaluacion(client, estudiante_headers, actividad_id)
            await client.post(
                f"/evaluaciones/{evaluacion['id']}/finalizar", headers=estudiante_headers
            )

            response = await client.post(
                f"/evaluaciones/{evaluacion['id']}/finalizar", headers=estudiante_headers
            )

        assert response.status_code == 422

    async def test_rechazo_por_evaluacion_inexistente(self, session):
        _estudiante, estudiante_headers = await _crear_estudiante(session)
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.post(
                f"/evaluaciones/{uuid.uuid4()}/finalizar", headers=estudiante_headers
            )

        assert response.status_code == 404

    async def test_rechazo_sin_autenticacion(self):
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.post(f"/evaluaciones/{uuid.uuid4()}/finalizar")

        assert response.status_code == 401

    async def test_rechazo_con_rol_insuficiente(self, docente_headers):
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.post(
                f"/evaluaciones/{uuid.uuid4()}/finalizar", headers=docente_headers
            )

        assert response.status_code == 403


class TestRevisionAPIIntegration:
    """Escenarios de revisión de
    `tests/features/inc3/US-3.2.3-finalizar-evaluacion-revision.feature`."""

    async def test_revision_disponible_tras_finalizar_con_correctas_e_incorrectas(
        self, session, docente_headers
    ):
        estudiante, estudiante_headers = await _crear_estudiante(session)
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            materia_id, banco_id = await _crear_materia(client, docente_headers)
            pregunta_correcta = await _cargar_verdadero_falso(
                client, docente_headers, banco_id, True
            )
            pregunta_incorrecta = await _cargar_verdadero_falso(
                client, docente_headers, banco_id, False
            )
            apertura = datetime.now(UTC) - timedelta(days=1)
            cierre = apertura + timedelta(days=7)
            actividad_id = await _crear_actividad(
                client, docente_headers, materia_id, 2, apertura, cierre
            )
            evaluacion = await _iniciar_evaluacion(client, estudiante_headers, actividad_id)
            ids_asignados = {
                p["pregunta_id"] for p in evaluacion["preguntas_asignadas"]
            }
            assert ids_asignados == {pregunta_correcta, pregunta_incorrecta}

            await client.post(
                f"/evaluaciones/{evaluacion['id']}/respuestas",
                json={"pregunta_id": pregunta_correcta, "contenido": {"valor": True}},
                headers=estudiante_headers,
            )
            await client.post(
                f"/evaluaciones/{evaluacion['id']}/respuestas",
                json={"pregunta_id": pregunta_incorrecta, "contenido": {"valor": True}},
                headers=estudiante_headers,
            )
            await client.post(
                f"/evaluaciones/{evaluacion['id']}/finalizar", headers=estudiante_headers
            )

            response = await client.get(
                f"/evaluaciones/{evaluacion['id']}/revision", headers=estudiante_headers
            )

        assert response.status_code == 200
        cuerpo = response.json()
        assert cuerpo["cantidad_preguntas"] == 2
        assert cuerpo["cantidad_correctas"] == 1
        assert cuerpo["cantidad_incorrectas"] == 1

        fila_correcta = next(
            f for f in cuerpo["detalle"] if f["pregunta_id"] == pregunta_correcta
        )
        assert fila_correcta["respondida"] is True
        assert fila_correcta["es_correcta"] is True
        assert fila_correcta["contenido_correcto"] is None

        fila_incorrecta = next(
            f for f in cuerpo["detalle"] if f["pregunta_id"] == pregunta_incorrecta
        )
        assert fila_incorrecta["respondida"] is True
        assert fila_incorrecta["es_correcta"] is False
        assert fila_incorrecta["contenido_correcto"] == {"valor": False}

    async def test_revision_incluye_no_respondidas_como_incorrectas(
        self, session, docente_headers
    ):
        estudiante, estudiante_headers = await _crear_estudiante(session)
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            materia_id, banco_id = await _crear_materia(client, docente_headers)
            pregunta_id = await _cargar_verdadero_falso(client, docente_headers, banco_id, True)
            apertura = datetime.now(UTC) - timedelta(days=1)
            cierre = apertura + timedelta(days=7)
            actividad_id = await _crear_actividad(
                client, docente_headers, materia_id, 1, apertura, cierre
            )
            evaluacion = await _iniciar_evaluacion(client, estudiante_headers, actividad_id)
            await client.post(
                f"/evaluaciones/{evaluacion['id']}/finalizar", headers=estudiante_headers
            )

            response = await client.get(
                f"/evaluaciones/{evaluacion['id']}/revision", headers=estudiante_headers
            )

        assert response.status_code == 200
        cuerpo = response.json()
        assert cuerpo["cantidad_correctas"] == 0
        assert cuerpo["cantidad_incorrectas"] == 1
        fila = cuerpo["detalle"][0]
        assert fila["pregunta_id"] == pregunta_id
        assert fila["respondida"] is False
        assert fila["contenido_propio"] is None
        assert fila["contenido_correcto"] == {"valor": True}

    async def test_revision_usa_la_respuesta_vigente_ante_reintentos(
        self, session, docente_headers
    ):
        estudiante, estudiante_headers = await _crear_estudiante(session)
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            materia_id, banco_id = await _crear_materia(client, docente_headers)
            pregunta_id = await _cargar_verdadero_falso(client, docente_headers, banco_id, True)
            apertura = datetime.now(UTC) - timedelta(days=1)
            cierre = apertura + timedelta(days=7)
            actividad_id = await _crear_actividad(
                client, docente_headers, materia_id, 1, apertura, cierre,
                cantidad_intentos_permitidos=2,
            )
            evaluacion = await _iniciar_evaluacion(client, estudiante_headers, actividad_id)
            await client.post(
                f"/evaluaciones/{evaluacion['id']}/respuestas",
                json={"pregunta_id": pregunta_id, "contenido": {"valor": False}},
                headers=estudiante_headers,
            )
            await client.post(
                f"/evaluaciones/{evaluacion['id']}/respuestas",
                json={"pregunta_id": pregunta_id, "contenido": {"valor": True}},
                headers=estudiante_headers,
            )
            await client.post(
                f"/evaluaciones/{evaluacion['id']}/finalizar", headers=estudiante_headers
            )

            response = await client.get(
                f"/evaluaciones/{evaluacion['id']}/revision", headers=estudiante_headers
            )

        cuerpo = response.json()
        fila = cuerpo["detalle"][0]
        assert fila["es_correcta"] is True
        assert fila["contenido_propio"] == {"valor": True}
        assert fila["contenido_correcto"] is None

    async def test_rechazo_de_la_revision_antes_de_finalizar_en_curso(
        self, session, docente_headers
    ):
        estudiante, estudiante_headers = await _crear_estudiante(session)
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            actividad_id, banco_id = await _actividad_vigente(client, docente_headers)
            evaluacion = await _iniciar_evaluacion(client, estudiante_headers, actividad_id)

            response = await client.get(
                f"/evaluaciones/{evaluacion['id']}/revision", headers=estudiante_headers
            )

        assert response.status_code == 422

    async def test_rechazo_de_la_revision_antes_de_finalizar_suspendida(
        self, session, docente_headers
    ):
        estudiante, estudiante_headers = await _crear_estudiante(session)
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            actividad_id, banco_id = await _actividad_vigente(client, docente_headers)
            evaluacion = await _iniciar_evaluacion(client, estudiante_headers, actividad_id)
            await client.post(
                f"/evaluaciones/{evaluacion['id']}/suspender", headers=estudiante_headers
            )

            response = await client.get(
                f"/evaluaciones/{evaluacion['id']}/revision", headers=estudiante_headers
            )

        assert response.status_code == 422

    async def test_rechazo_por_evaluacion_inexistente(self, session):
        _estudiante, estudiante_headers = await _crear_estudiante(session)
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.get(
                f"/evaluaciones/{uuid.uuid4()}/revision", headers=estudiante_headers
            )

        assert response.status_code == 404

    async def test_rechazo_sin_autenticacion(self):
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.get(f"/evaluaciones/{uuid.uuid4()}/revision")

        assert response.status_code == 401

    async def test_rechazo_con_rol_insuficiente(self, docente_headers):
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.get(
                f"/evaluaciones/{uuid.uuid4()}/revision", headers=docente_headers
            )

        assert response.status_code == 403
