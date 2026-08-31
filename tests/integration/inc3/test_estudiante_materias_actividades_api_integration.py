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


async def _crear_materia(client: AsyncClient, docente_headers: dict) -> str:
    nombre = f"Ingeniería de Software {uuid.uuid4()}"
    response = await client.post("/materias", json={"nombre": nombre}, headers=docente_headers)
    return response.json()["id"]


async def _crear_estudiante_de_materia(
    session, materia_id: str
) -> tuple[Usuario, dict[str, str]]:
    """Crea un Estudiante cuya comisión referencia una materia real de Banco de Preguntas.

    A diferencia de `_crear_estudiante` de `test_evaluaciones_api_integration.py` (comisión con
    `materia_id` aleatorio, alcanza para `IniciarEvaluacion`), acá el endpoint bajo prueba
    resuelve la materia vía `MateriaPort` — necesita un id real (`US-3.4.5`).
    """
    hasher = BcryptPasswordHasher()
    usuario_repo = SQLAlchemyUsuarioRepository(session)
    comision_repo = SQLAlchemyComisionRepository(session)

    admin = Usuario.crear(
        "Admin", f"admin.{uuid.uuid4()}@fiuner.edu.ar", hasher.hash("x"), TipoPerfil.ADMINISTRADOR
    )
    await usuario_repo.guardar(admin)
    comision = Comision.crear(uuid.UUID(materia_id), "lu 10-12", admin.id)
    await comision_repo.guardar(comision)

    estudiante = Usuario.crear_estudiante(
        "Estudiante", f"estudiante.{uuid.uuid4()}@fiuner.edu.ar", hasher.hash("x"), comision.id
    )
    await usuario_repo.guardar(estudiante)
    return estudiante, _headers_para(estudiante)


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


async def _crear_materia_con_preguntas(
    client: AsyncClient, docente_headers: dict, cantidad: int
) -> str:
    nombre = f"Ingeniería de Software {uuid.uuid4()}"
    creada = await client.post("/materias", json={"nombre": nombre}, headers=docente_headers)
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
            headers=docente_headers,
        )
    return creada.json()["id"]


class TestEstudianteMateriasAPIIntegration:
    """Escenarios de `tests/features/inc3/US-3.4.5-mis-materias-actividades.feature`."""

    async def test_estudiante_ve_su_materia(self, session, docente_headers):
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            materia_id = await _crear_materia(client, docente_headers)
            _estudiante, estudiante_headers = await _crear_estudiante_de_materia(
                session, materia_id
            )

            response = await client.get(
                "/identidad/estudiante/materias", headers=estudiante_headers
            )

        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["id"] == materia_id

    async def test_requiere_autenticacion(self):
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.get("/identidad/estudiante/materias")

        assert response.status_code == 401

    async def test_rol_docente_no_autorizado(self, docente_headers):
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.get(
                "/identidad/estudiante/materias", headers=docente_headers
            )

        assert response.status_code == 403


class TestActividadesVisiblesAPIIntegration:
    """Escenarios de `tests/features/inc3/US-3.4.5-mis-materias-actividades.feature`."""

    async def test_actividad_pendiente_dentro_del_periodo(self, session, docente_headers):
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            materia_id = await _crear_materia_con_preguntas(client, docente_headers, 5)
            _estudiante, estudiante_headers = await _crear_estudiante_de_materia(
                session, materia_id
            )
            apertura = datetime.now(UTC) - timedelta(days=1)
            cierre = apertura + timedelta(days=7)
            await _crear_actividad(client, docente_headers, materia_id, apertura, cierre)

            response = await client.get(
                f"/actividades/mis-actividades?materia_id={materia_id}",
                headers=estudiante_headers,
            )

        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["estado"] == "pendiente"
        assert data[0]["evaluacion_id"] is None

    async def test_actividad_todavia_no_abrio(self, session, docente_headers):
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            materia_id = await _crear_materia_con_preguntas(client, docente_headers, 5)
            _estudiante, estudiante_headers = await _crear_estudiante_de_materia(
                session, materia_id
            )
            apertura = datetime.now(UTC) + timedelta(days=1)
            cierre = apertura + timedelta(days=7)
            await _crear_actividad(client, docente_headers, materia_id, apertura, cierre)

            response = await client.get(
                f"/actividades/mis-actividades?materia_id={materia_id}",
                headers=estudiante_headers,
            )

        assert response.status_code == 200
        assert response.json()[0]["estado"] == "todavia_no_abrio"

    async def test_actividad_finalizada_por_el_estudiante(self, session, docente_headers):
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            materia_id = await _crear_materia_con_preguntas(client, docente_headers, 5)
            _estudiante, estudiante_headers = await _crear_estudiante_de_materia(
                session, materia_id
            )
            apertura = datetime.now(UTC) - timedelta(days=1)
            cierre = apertura + timedelta(days=7)
            actividad_id = await _crear_actividad(
                client, docente_headers, materia_id, apertura, cierre
            )

            iniciada = await client.post(
                "/evaluaciones",
                json={"actividad_id": actividad_id},
                headers=estudiante_headers,
            )
            evaluacion_id = iniciada.json()["id"]
            await client.post(
                f"/evaluaciones/{evaluacion_id}/finalizar", headers=estudiante_headers
            )

            response = await client.get(
                f"/actividades/mis-actividades?materia_id={materia_id}",
                headers=estudiante_headers,
            )

        assert response.status_code == 200
        data = response.json()
        assert data[0]["estado"] == "finalizada"
        assert data[0]["evaluacion_id"] == evaluacion_id
