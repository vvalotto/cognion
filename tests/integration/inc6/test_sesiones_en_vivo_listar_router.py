"""Tests HTTP de `GET /sesiones-en-vivo` (US-6.3.2).

Cubre uno a uno los escenarios de
`tests/features/inc6/US-6.3.2-listar-sesiones-en-vivo-comision.feature` contra la app real y la
base de datos local.
"""

from __future__ import annotations

import uuid

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
from src.shared.frameworks.db import SessionLocal
from tests.integration.inc6._helpers import (
    crear_estudiante,
    headers_de,
    iniciar_sesion,
    iniciar_y_finalizar,
    preparar_sesion,
)


def _cliente() -> AsyncClient:
    return AsyncClient(transport=ASGITransport(app=app), base_url="http://test")


def _docente() -> dict[str, str]:
    return headers_de(uuid.uuid4(), TipoPerfil.DOCENTE)


async def _get(params: dict, headers: dict[str, str]):
    async with _cliente() as client:
        return await client.get("/sesiones-en-vivo", params=params, headers=headers)


async def _crear_comision_sin_sesion() -> str:
    """Crea una Materia + Comisión reales, sin ninguna sesión en vivo — para el caso vacío."""
    admin = headers_de(uuid.uuid4(), TipoPerfil.ADMINISTRADOR)
    async with _cliente() as client:
        creada = await client.post(
            "/materias", json={"nombre": f"Materia {uuid.uuid4()}"}, headers=admin
        )
    materia_id = creada.json()["id"]
    async with SessionLocal() as session:
        admin_usuario = Usuario.crear(
            "Admin",
            f"admin.{uuid.uuid4()}@fiuner.edu.ar",
            BcryptPasswordHasher().hash("x"),
            TipoPerfil.ADMINISTRADOR,
        )
        await SQLAlchemyUsuarioRepository(session).guardar(admin_usuario)
        comision = Comision.crear(uuid.UUID(materia_id), "lu 10-12", admin_usuario.id)
        await SQLAlchemyComisionRepository(session).guardar(comision)
    return str(comision.id)


async def _crear_sesion(comision_id: str) -> str:
    """Crea una segunda sesión sobre una Comisión ya existente (mismo banco de preguntas)."""
    async with _cliente() as client:
        respuesta = await client.post(
            "/sesiones-en-vivo",
            json={
                "comision_id": comision_id,
                "cantidad_preguntas": 5,
                "tiempo_limite_por_pregunta_segundos": 30,
            },
            headers=_docente(),
        )
    assert respuesta.status_code == 201, respuesta.text
    return respuesta.json()["id"]


class TestListarComoDocente:
    async def test_recupera_la_sesion_activa_de_la_comision(self):
        sesion_id, comision_id = await preparar_sesion()
        await iniciar_sesion(sesion_id)

        response = await _get({"comision_id": comision_id}, _docente())

        assert response.status_code == 200
        cuerpo = response.json()
        assert len(cuerpo) == 1
        assert cuerpo[0]["id"] == sesion_id
        assert cuerpo[0]["estado"] == "EnCurso"
        assert cuerpo[0]["materia_nombre"]

    async def test_puede_pedir_tambien_las_finalizadas(self):
        sesion_id, comision_id = await preparar_sesion()
        await iniciar_y_finalizar(sesion_id)

        sin_finalizadas = await _get({"comision_id": comision_id}, _docente())
        con_finalizadas = await _get(
            {"comision_id": comision_id, "estado": "Finalizada"}, _docente()
        )

        assert sin_finalizadas.json() == []
        assert len(con_finalizadas.json()) == 1
        assert con_finalizadas.json()[0]["estado"] == "Finalizada"

    async def test_debe_indicar_la_comision(self):
        response = await _get({}, _docente())

        assert response.status_code == 422

    async def test_sin_sesiones_activas_devuelve_lista_vacia(self):
        comision_id = await _crear_comision_sin_sesion()

        response = await _get({"comision_id": comision_id}, _docente())

        assert response.status_code == 200
        assert response.json() == []


class TestListarComoEstudiante:
    async def test_ve_las_sesiones_de_su_comision(self):
        sesion_en_espera, comision_id = await preparar_sesion()
        sesion_en_curso = await _crear_sesion(comision_id)
        await iniciar_sesion(sesion_en_curso)
        _, headers = await crear_estudiante(comision_id)

        response = await _get({}, headers)

        assert response.status_code == 200
        ids = {s["id"] for s in response.json()}
        assert ids == {sesion_en_espera, sesion_en_curso}

    async def test_no_ve_sesiones_de_otra_comision(self):
        await preparar_sesion()
        comision_propia = await _crear_comision_sin_sesion()
        _, headers = await crear_estudiante(comision_propia)

        response = await _get({}, headers)

        assert response.status_code == 200
        assert response.json() == []

    async def test_sesiones_finalizadas_no_se_listan_por_defecto(self):
        sesion_id, comision_id = await preparar_sesion()
        await iniciar_y_finalizar(sesion_id)
        _, headers = await crear_estudiante(comision_id)

        response = await _get({}, headers)

        assert response.status_code == 200
        assert response.json() == []

    async def test_no_puede_pedir_otra_comision(self):
        _, comision_propia = await preparar_sesion()
        _, comision_de_otro = await preparar_sesion()
        _, headers = await crear_estudiante(comision_propia)

        response = await _get({"comision_id": comision_de_otro}, headers)

        assert response.status_code == 403


class TestOrden:
    async def test_orden_por_recientes(self):
        primera_sesion, comision_id = await preparar_sesion()
        segunda_sesion = await _crear_sesion(comision_id)

        response = await _get({"comision_id": comision_id}, _docente())

        assert response.status_code == 200
        assert [s["id"] for s in response.json()] == [segunda_sesion, primera_sesion]
