"""Preparación común de los escenarios de logging real (US-ADJ-64): tests de integración y BDD."""

from __future__ import annotations

import uuid

import httpx
import websockets
from websockets.exceptions import WebSocketException

from src.identidad.entities.comision import Comision
from src.identidad.entities.usuario import Usuario
from src.identidad.interface_adapters.gateways.comision_repository import (
    SQLAlchemyComisionRepository,
)
from src.identidad.interface_adapters.gateways.usuario_repository import SQLAlchemyUsuarioRepository
from src.shared.entities.tipo_perfil import TipoPerfil
from tests.integration.conftest import _id_desde_headers, asignar_docente_a_materia
from tests.integration.inc8._servidor_real import ServidorReal


async def materia_y_comision(
    servidor: ServidorReal,
    session,
    admin_headers: dict,
    docente_headers: dict,
    estudiantes: int = 0,
) -> tuple[str, str, list[str]]:
    """Crea una materia (por la API real), una comisión del Docente y sus estudiantes."""
    async with httpx.AsyncClient(base_url=servidor.url) as client:
        creada = await client.post(
            "/materias", json={"nombre": f"Materia {uuid.uuid4()}"}, headers=admin_headers
        )
    materia_id = creada.json()["id"]
    await asignar_docente_a_materia(materia_id, docente_headers)

    usuarios = SQLAlchemyUsuarioRepository(session)
    comisiones = SQLAlchemyComisionRepository(session)
    admin = Usuario.crear(
        "Admin", f"admin.{uuid.uuid4()}@fiuner.edu.ar", "hash", TipoPerfil.ADMINISTRADOR
    )
    await usuarios.guardar(admin)
    comision = Comision.crear(uuid.UUID(materia_id), "lu 10-12", admin.id)
    await comisiones.guardar(comision)
    comision.asignar_docente(_id_desde_headers(docente_headers))
    await comisiones.actualizar(comision)

    emails = []
    for i in range(estudiantes):
        email = f"estudiante{i}.{uuid.uuid4()}@fiuner.edu.ar"
        await usuarios.guardar(
            Usuario.crear_estudiante(f"Estudiante {i}", email, "hash", comision.id)
        )
        emails.append(email)
    return materia_id, str(comision.id), emails


async def intentar_websocket(servidor: ServidorReal, sesion_id: str, token: str) -> None:
    """Abre (o intenta abrir) el canal en vivo; el servidor registra la línea en cualquier caso."""
    url = f"ws://127.0.0.1:{servidor.puerto}/sesiones-en-vivo/{sesion_id}/canal?token={token}"
    try:
        async with websockets.connect(url, open_timeout=5):
            pass
    except (WebSocketException, OSError):
        pass
