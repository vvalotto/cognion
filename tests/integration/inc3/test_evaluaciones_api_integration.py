import uuid
from datetime import UTC, datetime, timedelta

from httpx import ASGITransport, AsyncClient

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


async def _crear_materia_con_preguntas(client: AsyncClient, headers: dict, cantidad: int) -> str:
    nombre = f"Ingeniería de Software {uuid.uuid4()}"
    creada = await client.post("/materias", json={"nombre": nombre}, headers=headers)
    banco_id = creada.json()["banco_id"]

    for i in range(cantidad):
        await client.post(
            "/preguntas/verdadero-falso",
            json={
                "banco_id": banco_id,
                "texto": f"Pregunta {i}",
                "respuesta_correcta": True,
                "unidad_tematica": "Unidad 1",
                "tema": "Tema",
                "dificultad": "medio",
                "importancia": "alto",
            },
            headers=headers,
        )

    return creada.json()["id"]


async def _crear_pregunta_opcion_multiple(
    client: AsyncClient, headers: dict, banco_id: str, texto: str, opciones: list[dict]
) -> None:
    await client.post(
        "/preguntas/opcion-multiple",
        json={
            "banco_id": banco_id,
            "texto": texto,
            "opciones": opciones,
            "unidad_tematica": "Unidad 1",
            "tema": "Tema",
            "dificultad": "medio",
            "importancia": "alto",
        },
        headers=headers,
    )


async def _crear_actividad(
    client: AsyncClient,
    docente_headers: dict,
    materia_id: str,
    cantidad_preguntas: int,
    apertura: datetime,
    cierre: datetime,
) -> str:
    response = await client.post(
        "/actividades",
        json={
            "materia_id": materia_id,
            "fecha_apertura": apertura.isoformat(),
            "fecha_cierre": cierre.isoformat(),
            "cantidad_preguntas": cantidad_preguntas,
            "cantidad_intentos_permitidos": 1,
        },
        headers=docente_headers,
    )
    return response.json()["id"]


class TestIniciarEvaluacionAPIIntegration:
    """Escenarios de `tests/features/inc3/US-3.1.3-iniciar-evaluacion.feature`."""

    async def test_estudiante_inicia_evaluacion_por_primera_vez(self, session, docente_headers):
        estudiante, estudiante_headers = await _crear_estudiante(session)
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            materia_id = await _crear_materia_con_preguntas(client, docente_headers, 20)
            apertura = datetime.now(UTC) - timedelta(days=1)
            cierre = apertura + timedelta(days=7)
            actividad_id = await _crear_actividad(
                client, docente_headers, materia_id, 10, apertura, cierre
            )

            response = await client.post(
                "/evaluaciones",
                json={"actividad_id": actividad_id},
                headers=estudiante_headers,
            )

        assert response.status_code == 200
        data = response.json()
        assert data["actividad_id"] == actividad_id
        assert data["estudiante_id"] == str(estudiante.id)
        assert data["estado"] == "EnCurso"
        assert len(data["preguntas_asignadas"]) == 10

    async def test_reconexion_es_idempotente(self, session, docente_headers):
        _estudiante, estudiante_headers = await _crear_estudiante(session)
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            materia_id = await _crear_materia_con_preguntas(client, docente_headers, 20)
            apertura = datetime.now(UTC) - timedelta(days=1)
            cierre = apertura + timedelta(days=7)
            actividad_id = await _crear_actividad(
                client, docente_headers, materia_id, 10, apertura, cierre
            )

            primera = await client.post(
                "/evaluaciones",
                json={"actividad_id": actividad_id},
                headers=estudiante_headers,
            )
            segunda = await client.post(
                "/evaluaciones",
                json={"actividad_id": actividad_id},
                headers=estudiante_headers,
            )

        assert primera.status_code == 200
        assert segunda.status_code == 200
        assert segunda.json()["id"] == primera.json()["id"]
        assert segunda.json()["preguntas_asignadas"] == primera.json()["preguntas_asignadas"]

    async def test_dos_estudiantes_reciben_evaluaciones_propias(self, session, docente_headers):
        estudiante_1, headers_1 = await _crear_estudiante(session)
        estudiante_2, headers_2 = await _crear_estudiante(session)
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            materia_id = await _crear_materia_con_preguntas(client, docente_headers, 20)
            apertura = datetime.now(UTC) - timedelta(days=1)
            cierre = apertura + timedelta(days=7)
            actividad_id = await _crear_actividad(
                client, docente_headers, materia_id, 10, apertura, cierre
            )

            respuesta_1 = await client.post(
                "/evaluaciones", json={"actividad_id": actividad_id}, headers=headers_1
            )
            respuesta_2 = await client.post(
                "/evaluaciones", json={"actividad_id": actividad_id}, headers=headers_2
            )

        assert respuesta_1.json()["id"] != respuesta_2.json()["id"]
        assert respuesta_1.json()["estudiante_id"] == str(estudiante_1.id)
        assert respuesta_2.json()["estudiante_id"] == str(estudiante_2.id)

    async def test_rechazo_antes_de_la_apertura(self, session, docente_headers):
        _estudiante, estudiante_headers = await _crear_estudiante(session)
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            materia_id = await _crear_materia_con_preguntas(client, docente_headers, 20)
            apertura = datetime.now(UTC) + timedelta(days=1)
            cierre = apertura + timedelta(days=7)
            actividad_id = await _crear_actividad(
                client, docente_headers, materia_id, 10, apertura, cierre
            )

            response = await client.post(
                "/evaluaciones",
                json={"actividad_id": actividad_id},
                headers=estudiante_headers,
            )

        assert response.status_code == 422

    async def test_rechazo_despues_del_cierre(self, session, docente_headers):
        _estudiante, estudiante_headers = await _crear_estudiante(session)
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            materia_id = await _crear_materia_con_preguntas(client, docente_headers, 20)
            cierre = datetime.now(UTC) - timedelta(days=1)
            apertura = cierre - timedelta(days=7)
            actividad_id = await _crear_actividad(
                client, docente_headers, materia_id, 10, apertura, cierre
            )

            response = await client.post(
                "/evaluaciones",
                json={"actividad_id": actividad_id},
                headers=estudiante_headers,
            )

        assert response.status_code == 422

    async def test_rechazo_por_actividad_inexistente(self, session):
        _estudiante, estudiante_headers = await _crear_estudiante(session)
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.post(
                "/evaluaciones",
                json={"actividad_id": str(uuid.uuid4())},
                headers=estudiante_headers,
            )

        assert response.status_code == 404

    async def test_rechazo_sin_autenticacion(self):
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.post("/evaluaciones", json={"actividad_id": str(uuid.uuid4())})

        assert response.status_code == 401

    async def test_rechazo_con_rol_insuficiente(self, docente_headers):
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.post(
                "/evaluaciones",
                json={"actividad_id": str(uuid.uuid4())},
                headers=docente_headers,
            )

        assert response.status_code == 403


class TestRendirEvaluacionAPIIntegration:
    """Escenarios de `tests/features/inc3/US-3.4.6-rendir-evaluacion.feature`."""

    async def test_preguntas_asignadas_traen_enunciado_y_opciones_sin_marcar_la_correcta(
        self, session, docente_headers
    ):
        estudiante, estudiante_headers = await _crear_estudiante(session)
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            nombre = f"Ingeniería de Software {uuid.uuid4()}"
            creada = await client.post("/materias", json={"nombre": nombre}, headers=docente_headers)
            banco_id = creada.json()["banco_id"]
            materia_id = creada.json()["id"]

            await _crear_pregunta_opcion_multiple(
                client,
                docente_headers,
                banco_id,
                "¿Cuál NO es un principio SOLID?",
                [
                    {"texto": "Responsabilidad única", "es_correcta": False},
                    {"texto": "Herencia múltiple obligatoria", "es_correcta": True},
                ],
            )
            await client.post(
                "/preguntas/verdadero-falso",
                json={
                    "banco_id": banco_id,
                    "texto": "Python es un lenguaje tipado dinámicamente.",
                    "respuesta_correcta": True,
                    "unidad_tematica": "Unidad 1",
                    "tema": "Tema",
                    "dificultad": "medio",
                    "importancia": "alto",
                },
                headers=docente_headers,
            )

            apertura = datetime.now(UTC) - timedelta(days=1)
            cierre = apertura + timedelta(days=7)
            actividad_id = await _crear_actividad(
                client, docente_headers, materia_id, 2, apertura, cierre
            )

            response = await client.post(
                "/evaluaciones",
                json={"actividad_id": actividad_id},
                headers=estudiante_headers,
            )

        assert response.status_code == 200
        data = response.json()
        assert data["preguntas_respondidas"] == []
        for asignada in data["preguntas_asignadas"]:
            assert asignada["enunciado"]
            if asignada["opciones"] is not None:
                assert asignada["opciones"] == [
                    "Responsabilidad única",
                    "Herencia múltiple obligatoria",
                ]
                for texto_opcion in asignada["opciones"]:
                    assert isinstance(texto_opcion, str)

    async def test_confirmar_una_respuesta_la_refleja_en_preguntas_respondidas(
        self, session, docente_headers
    ):
        _estudiante, estudiante_headers = await _crear_estudiante(session)
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            materia_id = await _crear_materia_con_preguntas(client, docente_headers, 5)
            apertura = datetime.now(UTC) - timedelta(days=1)
            cierre = apertura + timedelta(days=7)
            actividad_id = await _crear_actividad(
                client, docente_headers, materia_id, 3, apertura, cierre
            )

            iniciada = await client.post(
                "/evaluaciones",
                json={"actividad_id": actividad_id},
                headers=estudiante_headers,
            )
            evaluacion_id = iniciada.json()["id"]
            primera_pregunta_id = iniciada.json()["preguntas_asignadas"][0]["pregunta_id"]

            await client.post(
                f"/evaluaciones/{evaluacion_id}/respuestas",
                json={"pregunta_id": primera_pregunta_id, "contenido": {"valor": True}},
                headers=estudiante_headers,
            )

            reconexion = await client.post(
                "/evaluaciones",
                json={"actividad_id": actividad_id},
                headers=estudiante_headers,
            )

        assert reconexion.status_code == 200
        assert reconexion.json()["preguntas_respondidas"] == [primera_pregunta_id]
        assert reconexion.json()["estado"] == "EnCurso"

    async def test_pausar_y_reanudar_conserva_el_set_y_las_respuestas(
        self, session, docente_headers
    ):
        _estudiante, estudiante_headers = await _crear_estudiante(session)
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            materia_id = await _crear_materia_con_preguntas(client, docente_headers, 5)
            apertura = datetime.now(UTC) - timedelta(days=1)
            cierre = apertura + timedelta(days=7)
            actividad_id = await _crear_actividad(
                client, docente_headers, materia_id, 3, apertura, cierre
            )

            iniciada = await client.post(
                "/evaluaciones",
                json={"actividad_id": actividad_id},
                headers=estudiante_headers,
            )
            evaluacion_id = iniciada.json()["id"]
            preguntas_asignadas = iniciada.json()["preguntas_asignadas"]

            await client.post(
                f"/evaluaciones/{evaluacion_id}/respuestas",
                json={
                    "pregunta_id": preguntas_asignadas[0]["pregunta_id"],
                    "contenido": {"valor": True},
                },
                headers=estudiante_headers,
            )

            suspendida = await client.post(
                f"/evaluaciones/{evaluacion_id}/suspender", headers=estudiante_headers
            )

            reingreso = await client.post(
                "/evaluaciones",
                json={"actividad_id": actividad_id},
                headers=estudiante_headers,
            )

            reanudada = await client.post(
                f"/evaluaciones/{evaluacion_id}/reanudar", headers=estudiante_headers
            )

        assert suspendida.status_code == 200
        assert suspendida.json()["estado"] == "Suspendida"

        assert reingreso.status_code == 200
        assert reingreso.json()["estado"] == "Suspendida"
        assert reingreso.json()["id"] == evaluacion_id
        assert reingreso.json()["preguntas_asignadas"] == preguntas_asignadas

        assert reanudada.status_code == 200
        assert reanudada.json()["estado"] == "EnCurso"
        assert reanudada.json()["preguntas_respondidas"] == [
            preguntas_asignadas[0]["pregunta_id"]
        ]
        assert reanudada.json()["preguntas_asignadas"] == preguntas_asignadas
