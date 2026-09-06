"""Tests de integración HTTP de los endpoints de consulta de comisiones (US-4.2.2).

Cubre los escenarios de `tests/features/inc4/US-4.2.2-comision-query-port.feature`.
"""

import uuid

from httpx import ASGITransport, AsyncClient

from src.app import app
from src.identidad.entities.comision import Comision
from src.identidad.entities.usuario import Usuario
from src.identidad.interface_adapters.gateways.comision_repository import (
    SQLAlchemyComisionRepository,
)
from src.identidad.interface_adapters.gateways.usuario_repository import SQLAlchemyUsuarioRepository
from src.shared.entities.tipo_perfil import TipoPerfil
from src.shared.frameworks.security.jwt_pyjwt import PyJWTIssuer


def _headers_estudiante() -> dict[str, str]:
    jwt_vo = PyJWTIssuer().emitir(uuid.uuid4(), TipoPerfil.ESTUDIANTE)
    return {"Authorization": f"Bearer {jwt_vo.token}"}


async def _crear_materia(client, docente_headers, nombre: str) -> str:
    response = await client.post("/materias", json={"nombre": nombre}, headers=docente_headers)
    return response.json()["id"]


class TestListarComisionesPorMateria:
    async def test_materia_con_comisiones(self, session, docente_headers, admin_headers):
        admin = Usuario.crear(
            "Vic", f"vic.{uuid.uuid4()}@fiuner.edu.ar", "hash", TipoPerfil.ADMINISTRADOR
        )
        await SQLAlchemyUsuarioRepository(session).guardar(admin)
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            materia_id = await _crear_materia(client, docente_headers, f"IS {uuid.uuid4()}")
            comision_repo = SQLAlchemyComisionRepository(session)
            comision_1 = Comision.crear(uuid.UUID(materia_id), "lu 10-12", admin.id)
            comision_2 = Comision.crear(uuid.UUID(materia_id), "ma 14-16", admin.id)
            await comision_repo.guardar(comision_1)
            await comision_repo.guardar(comision_2)

            response = await client.get(
                f"/materias/{materia_id}/comisiones", headers=docente_headers
            )

        assert response.status_code == 200
        ids = {c["id"] for c in response.json()}
        assert ids == {str(comision_1.id), str(comision_2.id)}

    async def test_materia_inexistente_devuelve_404(self, docente_headers):
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.get(
                f"/materias/{uuid.uuid4()}/comisiones", headers=docente_headers
            )

        assert response.status_code == 404

    async def test_rol_distinto_de_docente_devuelve_403(self, docente_headers):
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            materia_id = await _crear_materia(client, docente_headers, f"IS {uuid.uuid4()}")

            response = await client.get(
                f"/materias/{materia_id}/comisiones", headers=_headers_estudiante()
            )

        assert response.status_code == 403


class TestListarEstudiantes:
    async def test_comision_con_estudiantes(self, session, admin_headers, docente_headers):
        usuario_repo = SQLAlchemyUsuarioRepository(session)
        comision_repo = SQLAlchemyComisionRepository(session)
        admin = Usuario.crear(
            "Vic", f"vic.{uuid.uuid4()}@fiuner.edu.ar", "hash", TipoPerfil.ADMINISTRADOR
        )
        await usuario_repo.guardar(admin)
        comision = Comision.crear(uuid.uuid4(), "lu 10-12", admin.id)
        await comision_repo.guardar(comision)
        estudiante = Usuario.crear_estudiante(
            "Ana Pérez", f"ana.{uuid.uuid4()}@fiuner.edu.ar", "hash", comision.id
        )
        await usuario_repo.guardar(estudiante)

        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.get(
                f"/comisiones/{comision.id}/estudiantes", headers=docente_headers
            )

        assert response.status_code == 200
        assert response.json() == [{"id": str(estudiante.id), "nombre": "Ana Pérez"}]

    async def test_comision_sin_estudiantes_devuelve_lista_vacia(
        self, session, admin_headers, docente_headers
    ):
        usuario_repo = SQLAlchemyUsuarioRepository(session)
        comision_repo = SQLAlchemyComisionRepository(session)
        admin = Usuario.crear(
            "Vic", f"vic.{uuid.uuid4()}@fiuner.edu.ar", "hash", TipoPerfil.ADMINISTRADOR
        )
        await usuario_repo.guardar(admin)
        comision = Comision.crear(uuid.uuid4(), "lu 10-12", admin.id)
        await comision_repo.guardar(comision)

        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.get(
                f"/comisiones/{comision.id}/estudiantes", headers=docente_headers
            )

        assert response.status_code == 200
        assert response.json() == []

    async def test_comision_inexistente_devuelve_404(self, docente_headers):
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.get(
                f"/comisiones/{uuid.uuid4()}/estudiantes", headers=docente_headers
            )

        assert response.status_code == 404
