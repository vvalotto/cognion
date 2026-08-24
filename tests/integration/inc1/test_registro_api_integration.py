import uuid
from datetime import UTC, datetime, timedelta

from httpx import ASGITransport, AsyncClient

from src.app import app
from src.banco_preguntas.entities.materia import Materia
from src.banco_preguntas.interface_adapters.gateways.materia_repository import (
    SQLAlchemyMateriaRepository,
)
from src.identidad.entities.comision import Comision
from src.identidad.entities.invitacion import Invitacion
from src.identidad.entities.usuario import Usuario
from src.identidad.frameworks.db.models import InvitacionModel
from src.identidad.interface_adapters.gateways.comision_repository import (
    SQLAlchemyComisionRepository,
)
from src.identidad.interface_adapters.gateways.invitacion_repository import (
    SQLAlchemyInvitacionRepository,
)
from src.identidad.interface_adapters.gateways.usuario_repository import SQLAlchemyUsuarioRepository
from src.shared.entities.tipo_perfil import TipoPerfil

_NOMBRE_MATERIA = "IS-2026-C1"


async def _crear_invitacion_vigente(session) -> tuple[Invitacion, str]:
    usuario_repo = SQLAlchemyUsuarioRepository(session)
    comision_repo = SQLAlchemyComisionRepository(session)
    invitacion_repo = SQLAlchemyInvitacionRepository(session)
    materia_repo = SQLAlchemyMateriaRepository(session)

    sufijo = uuid.uuid4()
    materia = Materia.crear(f"{_NOMBRE_MATERIA} {sufijo}")
    await materia_repo.guardar(materia)
    admin = Usuario.crear("Vic", f"vic.{sufijo}@fiuner.edu.ar", "hash", TipoPerfil.ADMINISTRADOR)
    await usuario_repo.guardar(admin)
    docente = Usuario.crear("Ana", f"ana.{sufijo}@fiuner.edu.ar", "hash", TipoPerfil.DOCENTE)
    await usuario_repo.guardar(docente)
    comision = Comision.crear(materia.id, "lu 10-12", admin.id)
    await comision_repo.guardar(comision)

    invitacion = Invitacion.crear(comision.id, docente.id)
    await invitacion_repo.guardar(invitacion)
    return invitacion, materia.nombre


class TestRegistroAPIIntegration:
    async def test_registro_exitoso_con_invitacion_vigente(self, session):
        invitacion, nombre_materia = await _crear_invitacion_vigente(session)

        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.post(
                "/identidad/registro",
                json={
                    "token": invitacion.token,
                    "nombre": "Nico Estudiante",
                    "email": "nico.reg@fiuner.edu.ar",
                    "password": "claveSegura1",
                },
            )

        assert response.status_code == 201
        data = response.json()
        assert data["email"] == "nico.reg@fiuner.edu.ar"
        assert data["comision_id"] == str(invitacion.comision_id)
        assert data["materia"] == nombre_materia

    async def test_registro_rechaza_email_ya_registrado(self, session):
        invitacion, _nombre_materia = await _crear_invitacion_vigente(session)

        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            primera = await client.post(
                "/identidad/registro",
                json={
                    "token": invitacion.token,
                    "nombre": "Nico Estudiante",
                    "email": "duplicado.reg@fiuner.edu.ar",
                    "password": "claveSegura1",
                },
            )
            assert primera.status_code == 201

            otra_invitacion, _otro_nombre = await _crear_invitacion_vigente(session)
            segunda = await client.post(
                "/identidad/registro",
                json={
                    "token": otra_invitacion.token,
                    "nombre": "Otro",
                    "email": "duplicado.reg@fiuner.edu.ar",
                    "password": "claveSegura1",
                },
            )

        assert segunda.status_code == 409

    async def test_registro_rechaza_invitacion_vencida(self, session):
        invitacion, _nombre_materia = await _crear_invitacion_vigente(session)
        modelo = await session.get(InvitacionModel, invitacion.id)
        modelo.expira_en = datetime.now(UTC) - timedelta(days=1)
        await session.commit()

        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.post(
                "/identidad/registro",
                json={
                    "token": invitacion.token,
                    "nombre": "Nico Estudiante",
                    "email": "vencida.reg@fiuner.edu.ar",
                    "password": "claveSegura1",
                },
            )

        assert response.status_code == 422

    async def test_registro_rechaza_invitacion_ya_usada(self, session):
        invitacion, _nombre_materia = await _crear_invitacion_vigente(session)
        modelo = await session.get(InvitacionModel, invitacion.id)
        modelo.usada_en = datetime.now(UTC)
        await session.commit()

        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.post(
                "/identidad/registro",
                json={
                    "token": invitacion.token,
                    "nombre": "Nico Estudiante",
                    "email": "yausada.reg@fiuner.edu.ar",
                    "password": "claveSegura1",
                },
            )

        assert response.status_code == 422

    async def test_registro_rechaza_token_inexistente(self, session):
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.post(
                "/identidad/registro",
                json={
                    "token": "token-inexistente",
                    "nombre": "Nico Estudiante",
                    "email": "inexistente.reg@fiuner.edu.ar",
                    "password": "claveSegura1",
                },
            )

        assert response.status_code == 422
