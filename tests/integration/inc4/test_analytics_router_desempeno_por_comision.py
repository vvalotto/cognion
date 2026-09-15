"""Tests de integración de `GET /analytics/.../comisiones/{id}/desempeno` (US-ADJ-44, RF-20).

Escribe una `Comision` real (Identidad), crea una `ActividadEvaluativaPeriodoAbierto` real vía
API (Actividad Evaluativa) y ejercita el endpoint completo — router → controller → use case →
los 2 adapters (`US-4.1.1`/`US-4.2.2`, más `listar_actividades_abiertas` nuevo) — vía
`AsyncClient`, mismos escenarios que
`tests/features/inc5-adj/US-ADJ-44-desempeno-por-comision.feature`.
"""

from __future__ import annotations

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


async def _comision_con_estudiante(session, materia_id) -> tuple[uuid.UUID, Usuario, dict]:
    hasher = BcryptPasswordHasher()
    usuario_repo = SQLAlchemyUsuarioRepository(session)
    comision_repo = SQLAlchemyComisionRepository(session)

    admin = Usuario.crear(
        "Admin", f"admin.{uuid.uuid4()}@fiuner.edu.ar", hasher.hash("x"), TipoPerfil.ADMINISTRADOR
    )
    await usuario_repo.guardar(admin)
    comision = Comision.crear(materia_id, "lu 10-12", admin.id)
    await comision_repo.guardar(comision)

    estudiante = Usuario.crear_estudiante(
        "Estudiante", f"estudiante.{uuid.uuid4()}@fiuner.edu.ar", hasher.hash("x"), comision.id
    )
    await usuario_repo.guardar(estudiante)
    return comision.id, estudiante, _headers_para(estudiante)


async def _crear_materia(client: AsyncClient, headers: dict) -> tuple[str, str]:
    nombre = f"Ingeniería de Software {uuid.uuid4()}"
    creada = await client.post("/materias", json={"nombre": nombre}, headers=headers)
    return creada.json()["id"], creada.json()["banco_id"]


async def _cargar_verdadero_falso(client: AsyncClient, headers: dict, banco_id: str) -> str:
    respuesta = await client.post(
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
    return respuesta.json()["id"]


async def _crear_actividad(
    client: AsyncClient,
    docente_headers: dict,
    materia_id: str,
    apertura: datetime,
    cierre: datetime,
    comisiones_ids: list[str] | None = None,
) -> str:
    response = await client.post(
        "/actividades",
        json={
            "materia_id": materia_id,
            "fecha_apertura": apertura.isoformat(),
            "fecha_cierre": cierre.isoformat(),
            "cantidad_preguntas": 1,
            "cantidad_intentos_permitidos": 1,
            "comisiones_ids": comisiones_ids or [],
        },
        headers=docente_headers,
    )
    return response.json()["id"]


async def _rendir_y_finalizar(client: AsyncClient, headers: dict, actividad_id: str) -> None:
    """Rinde respondiendo correctamente todas las preguntas asignadas, luego finaliza."""
    evaluacion = (
        await client.post("/evaluaciones", json={"actividad_id": actividad_id}, headers=headers)
    ).json()
    for pregunta in evaluacion["preguntas_asignadas"]:
        await client.post(
            f"/evaluaciones/{evaluacion['id']}/respuestas",
            json={"pregunta_id": pregunta["pregunta_id"], "contenido": {"valor": True}},
            headers=headers,
        )
    await client.post(f"/evaluaciones/{evaluacion['id']}/finalizar", headers=headers)


class TestAnalyticsRouterDesempenoPorComision:
    """Escenarios de `tests/features/inc5-adj/US-ADJ-44-desempeno-por-comision.feature`."""

    async def test_estudiante_con_evaluacion_finalizada_y_actividad_pendiente(
        self, session, docente_headers, admin_headers
    ):
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            materia_id, banco_id = await _crear_materia(client, admin_headers)
            await _cargar_verdadero_falso(client, docente_headers, banco_id)
            comision_id, estudiante, estudiante_headers = await _comision_con_estudiante(
                session, materia_id
            )
            ahora = datetime.now(UTC)
            actividad_rendida = await _crear_actividad(
                client,
                docente_headers,
                materia_id,
                ahora - timedelta(days=1),
                ahora + timedelta(days=7),
            )
            await _rendir_y_finalizar(client, estudiante_headers, actividad_rendida)
            await _cargar_verdadero_falso(client, docente_headers, banco_id)
            await _crear_actividad(
                client,
                docente_headers,
                materia_id,
                ahora - timedelta(days=1),
                ahora + timedelta(days=7),
            )

            response = await client.get(
                f"/analytics/materias/{materia_id}/comisiones/{comision_id}/desempeno",
                headers=docente_headers,
            )

        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["estudiante_id"] == str(estudiante.id)
        assert data[0]["porcentaje_aciertos_acumulado"] == 100.0
        assert data[0]["actividades_pendientes"] == 1

    async def test_comision_sin_evaluaciones_finalizadas(self, session, docente_headers, admin_headers):
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            materia_id, _banco_id = await _crear_materia(client, admin_headers)
            comision_id, estudiante, _headers = await _comision_con_estudiante(session, materia_id)

            response = await client.get(
                f"/analytics/materias/{materia_id}/comisiones/{comision_id}/desempeno",
                headers=docente_headers,
            )

        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["estudiante_id"] == str(estudiante.id)
        assert data[0]["porcentaje_aciertos_acumulado"] is None
        assert data[0]["actividades_pendientes"] == 0

    async def test_comision_que_no_pertenece_a_la_materia(self, session, docente_headers, admin_headers):
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            materia_id, _banco_id = await _crear_materia(client, admin_headers)
            otra_materia_id = uuid.uuid4()
            comision_de_otra_materia, _est, _h = await _comision_con_estudiante(
                session, otra_materia_id
            )

            response = await client.get(
                f"/analytics/materias/{materia_id}/comisiones/{comision_de_otra_materia}/desempeno",
                headers=docente_headers,
            )

        assert response.status_code == 422

    async def test_sin_autenticacion(self):
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.get(
                f"/analytics/materias/{uuid.uuid4()}/comisiones/{uuid.uuid4()}/desempeno"
            )

        assert response.status_code == 401

    async def test_rol_distinto_de_docente(self):
        jwt_vo = PyJWTIssuer().emitir(uuid.uuid4(), TipoPerfil.ESTUDIANTE)
        headers = {"Authorization": f"Bearer {jwt_vo.token}"}
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.get(
                f"/analytics/materias/{uuid.uuid4()}/comisiones/{uuid.uuid4()}/desempeno",
                headers=headers,
            )

        assert response.status_code == 403
