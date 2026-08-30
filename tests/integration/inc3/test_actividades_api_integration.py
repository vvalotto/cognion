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


def _periodo() -> tuple[str, str]:
    apertura = datetime.now(UTC)
    cierre = apertura + timedelta(days=7)
    return apertura.isoformat(), cierre.isoformat()


class TestCrearActividadAPIIntegration:
    """Escenarios de `tests/features/inc3/US-3.1.2-crear-actividad-periodo-abierto.feature`."""

    async def test_docente_crea_actividad_valida(self, docente_headers):
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            materia_id = await _crear_materia_con_preguntas(client, docente_headers, 20)
            apertura, cierre = _periodo()

            response = await client.post(
                "/actividades",
                json={
                    "materia_id": materia_id,
                    "fecha_apertura": apertura,
                    "fecha_cierre": cierre,
                    "cantidad_preguntas": 10,
                    "cantidad_intentos_permitidos": 1,
                },
                headers=docente_headers,
            )

        assert response.status_code == 201
        data = response.json()
        assert data["materia_id"] == materia_id
        assert data["cantidad_preguntas"] == 10
        assert data["cantidad_intentos_permitidos"] == 1
        assert data["cerrada_manualmente"] is False
        assert data["titulo"] == ""
        assert "id" in data

    async def test_docente_crea_actividad_con_titulo(self, docente_headers):
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            materia_id = await _crear_materia_con_preguntas(client, docente_headers, 20)
            apertura, cierre = _periodo()

            response = await client.post(
                "/actividades",
                json={
                    "materia_id": materia_id,
                    "fecha_apertura": apertura,
                    "fecha_cierre": cierre,
                    "cantidad_preguntas": 10,
                    "cantidad_intentos_permitidos": 1,
                    "titulo": "Parcial 1 — Unidades 1 a 3",
                },
                headers=docente_headers,
            )

        assert response.status_code == 201
        assert response.json()["titulo"] == "Parcial 1 — Unidades 1 a 3"

    async def test_rechazo_por_preguntas_insuficientes(self, docente_headers):
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            materia_id = await _crear_materia_con_preguntas(client, docente_headers, 5)
            apertura, cierre = _periodo()

            response = await client.post(
                "/actividades",
                json={
                    "materia_id": materia_id,
                    "fecha_apertura": apertura,
                    "fecha_cierre": cierre,
                    "cantidad_preguntas": 10,
                    "cantidad_intentos_permitidos": 1,
                },
                headers=docente_headers,
            )

        assert response.status_code == 422

    async def test_rechazo_por_periodo_invalido(self, docente_headers):
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            materia_id = await _crear_materia_con_preguntas(client, docente_headers, 20)
            apertura, cierre = _periodo()

            response = await client.post(
                "/actividades",
                json={
                    "materia_id": materia_id,
                    "fecha_apertura": cierre,
                    "fecha_cierre": apertura,
                    "cantidad_preguntas": 10,
                    "cantidad_intentos_permitidos": 1,
                },
                headers=docente_headers,
            )

        assert response.status_code == 422

    async def test_rechazo_por_cantidad_intentos_invalida(self, docente_headers):
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            materia_id = await _crear_materia_con_preguntas(client, docente_headers, 20)
            apertura, cierre = _periodo()

            response = await client.post(
                "/actividades",
                json={
                    "materia_id": materia_id,
                    "fecha_apertura": apertura,
                    "fecha_cierre": cierre,
                    "cantidad_preguntas": 10,
                    "cantidad_intentos_permitidos": 0,
                },
                headers=docente_headers,
            )

        assert response.status_code == 422

    async def test_rechazo_por_materia_inexistente(self, docente_headers):
        transport = ASGITransport(app=app)
        apertura, cierre = _periodo()
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.post(
                "/actividades",
                json={
                    "materia_id": str(uuid.uuid4()),
                    "fecha_apertura": apertura,
                    "fecha_cierre": cierre,
                    "cantidad_preguntas": 10,
                    "cantidad_intentos_permitidos": 1,
                },
                headers=docente_headers,
            )

        assert response.status_code == 404

    async def test_rechazo_sin_autenticacion(self):
        transport = ASGITransport(app=app)
        apertura, cierre = _periodo()
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.post(
                "/actividades",
                json={
                    "materia_id": str(uuid.uuid4()),
                    "fecha_apertura": apertura,
                    "fecha_cierre": cierre,
                    "cantidad_preguntas": 10,
                    "cantidad_intentos_permitidos": 1,
                },
            )

        assert response.status_code == 401

    async def test_rechazo_con_rol_insuficiente(self, admin_headers):
        transport = ASGITransport(app=app)
        apertura, cierre = _periodo()
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.post(
                "/actividades",
                json={
                    "materia_id": str(uuid.uuid4()),
                    "fecha_apertura": apertura,
                    "fecha_cierre": cierre,
                    "cantidad_preguntas": 10,
                    "cantidad_intentos_permitidos": 1,
                },
                headers=admin_headers,
            )

        assert response.status_code == 403


class TestListarActividadesAPIIntegration:
    """Escenarios de `tests/features/inc3/US-3.4.2-listado-materias-actividades-docente.feature`."""

    async def test_lista_actividad_en_curso_con_conteo_de_activas(self, session, docente_headers):
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            materia_id = await _crear_materia_con_preguntas(client, docente_headers, 20)
            estudiante_headers = await _crear_estudiante(session)
            apertura, cierre = _periodo()

            crear = await client.post(
                "/actividades",
                json={
                    "materia_id": materia_id,
                    "fecha_apertura": apertura,
                    "fecha_cierre": cierre,
                    "cantidad_preguntas": 10,
                    "cantidad_intentos_permitidos": 1,
                    "titulo": "Parcial 1",
                },
                headers=docente_headers,
            )
            actividad_id = crear.json()["id"]
            await client.post(
                "/evaluaciones", json={"actividad_id": actividad_id}, headers=estudiante_headers
            )

            response = await client.get(
                "/actividades", params={"materia_id": materia_id}, headers=docente_headers
            )

        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["id"] == actividad_id
        assert data[0]["titulo"] == "Parcial 1"
        assert data[0]["estado"] == "en_curso"
        assert data[0]["cantidad_evaluaciones_activas"] == 1
        assert data[0]["cantidad_evaluaciones_finalizadas"] == 0

    async def test_actividad_con_apertura_futura_es_programada(self, docente_headers):
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            materia_id = await _crear_materia_con_preguntas(client, docente_headers, 20)
            apertura = datetime.now(UTC) + timedelta(days=1)
            cierre = apertura + timedelta(days=7)

            await client.post(
                "/actividades",
                json={
                    "materia_id": materia_id,
                    "fecha_apertura": apertura.isoformat(),
                    "fecha_cierre": cierre.isoformat(),
                    "cantidad_preguntas": 10,
                    "cantidad_intentos_permitidos": 1,
                },
                headers=docente_headers,
            )

            response = await client.get(
                "/actividades", params={"materia_id": materia_id}, headers=docente_headers
            )

        data = response.json()
        assert data[0]["estado"] == "programada"
        assert data[0]["cantidad_evaluaciones_activas"] == 0

    async def test_actividad_cerrada_manualmente(self, docente_headers):
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            materia_id = await _crear_materia_con_preguntas(client, docente_headers, 20)
            apertura, cierre = _periodo()

            crear = await client.post(
                "/actividades",
                json={
                    "materia_id": materia_id,
                    "fecha_apertura": apertura,
                    "fecha_cierre": cierre,
                    "cantidad_preguntas": 10,
                    "cantidad_intentos_permitidos": 1,
                },
                headers=docente_headers,
            )
            actividad_id = crear.json()["id"]
            await client.post(f"/actividades/{actividad_id}/cerrar", headers=docente_headers)

            response = await client.get(
                "/actividades", params={"materia_id": materia_id}, headers=docente_headers
            )

        data = response.json()
        assert data[0]["estado"] == "cerrada"

    async def test_materia_sin_actividades_devuelve_lista_vacia(self, docente_headers):
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            materia_id = await _crear_materia_con_preguntas(client, docente_headers, 20)

            response = await client.get(
                "/actividades", params={"materia_id": materia_id}, headers=docente_headers
            )

        assert response.status_code == 200
        assert response.json() == []

    async def test_rechazo_sin_autenticacion(self):
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.get("/actividades", params={"materia_id": str(uuid.uuid4())})

        assert response.status_code == 401

    async def test_rechazo_con_rol_insuficiente(self, admin_headers):
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.get(
                "/actividades", params={"materia_id": str(uuid.uuid4())}, headers=admin_headers
            )

        assert response.status_code == 403


class TestObtenerActividadAPIIntegration:
    """Escenarios de `tests/features/inc3/US-3.4.4-detalle-actividad.feature`."""

    async def test_obtiene_el_detalle_con_conteos_y_estado(self, session, docente_headers):
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            materia_id = await _crear_materia_con_preguntas(client, docente_headers, 20)
            estudiante_headers = await _crear_estudiante(session)
            apertura, cierre = _periodo()

            crear = await client.post(
                "/actividades",
                json={
                    "materia_id": materia_id,
                    "fecha_apertura": apertura,
                    "fecha_cierre": cierre,
                    "cantidad_preguntas": 10,
                    "cantidad_intentos_permitidos": 1,
                    "titulo": "Parcial 1",
                },
                headers=docente_headers,
            )
            actividad_id = crear.json()["id"]
            await client.post(
                "/evaluaciones", json={"actividad_id": actividad_id}, headers=estudiante_headers
            )

            response = await client.get(f"/actividades/{actividad_id}", headers=docente_headers)

        assert response.status_code == 200
        data = response.json()
        assert data["id"] == actividad_id
        assert data["titulo"] == "Parcial 1"
        assert data["cantidad_preguntas"] == 10
        assert data["cantidad_intentos_permitidos"] == 1
        assert data["estado"] == "en_curso"
        assert data["cerrada_manualmente"] is False
        assert data["cantidad_evaluaciones_activas"] == 1
        assert data["cantidad_evaluaciones_finalizadas"] == 0

    async def test_detalle_de_actividad_cerrada_manualmente(self, docente_headers):
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            materia_id = await _crear_materia_con_preguntas(client, docente_headers, 20)
            apertura, cierre = _periodo()

            crear = await client.post(
                "/actividades",
                json={
                    "materia_id": materia_id,
                    "fecha_apertura": apertura,
                    "fecha_cierre": cierre,
                    "cantidad_preguntas": 10,
                    "cantidad_intentos_permitidos": 1,
                },
                headers=docente_headers,
            )
            actividad_id = crear.json()["id"]
            await client.post(f"/actividades/{actividad_id}/cerrar", headers=docente_headers)

            response = await client.get(f"/actividades/{actividad_id}", headers=docente_headers)

        data = response.json()
        assert data["estado"] == "cerrada"
        assert data["cerrada_manualmente"] is True

    async def test_rechazo_por_actividad_inexistente(self, docente_headers):
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.get(
                f"/actividades/{uuid.uuid4()}", headers=docente_headers
            )

        assert response.status_code == 404

    async def test_rechazo_sin_autenticacion(self):
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.get(f"/actividades/{uuid.uuid4()}")

        assert response.status_code == 401

    async def test_rechazo_con_rol_insuficiente(self, admin_headers):
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.get(
                f"/actividades/{uuid.uuid4()}", headers=admin_headers
            )

        assert response.status_code == 403
