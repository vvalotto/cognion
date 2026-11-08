"""Ayudas compartidas por los tests de integración y BDD del link grupal (US-ADJ-67).

Siembran una comisión con su Docente y llaman a la API por HTTP; requieren una base descartable.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta

from httpx import ASGITransport, AsyncClient, Response
from sqlalchemy import update

from src.app import app
from src.banco_preguntas.entities.materia import Materia
from src.banco_preguntas.interface_adapters.gateways.materia_repository import (
    SQLAlchemyMateriaRepository,
)
from src.identidad.entities.comision import Comision
from src.identidad.entities.usuario import Usuario
from src.identidad.frameworks.db.models import InvitacionModel
from src.identidad.interface_adapters.gateways.comision_repository import (
    SQLAlchemyComisionRepository,
)
from src.identidad.interface_adapters.gateways.usuario_repository import SQLAlchemyUsuarioRepository
from src.shared.entities.tipo_perfil import TipoPerfil
from src.shared.frameworks.security.jwt_pyjwt import PyJWTIssuer

PASSWORD = "Clave#Segura-2026"


@dataclass
class Escenario:
    """Una comisión con su Docente asignado y los encabezados de ese Docente."""

    comision_id: uuid.UUID
    docente_id: uuid.UUID
    headers: dict[str, str]


def _headers(usuario_id: uuid.UUID, rol: TipoPerfil = TipoPerfil.DOCENTE) -> dict[str, str]:
    return {"Authorization": f"Bearer {PyJWTIssuer().emitir(usuario_id, rol).token}"}


async def _escenario(session) -> Escenario:
    sufijo = uuid.uuid4()
    materia = Materia.crear(f"IS {sufijo}")
    await SQLAlchemyMateriaRepository(session).guardar(materia)
    usuarios = SQLAlchemyUsuarioRepository(session)
    admin = Usuario.crear("Vic", f"vic.{sufijo}@fiuner.edu.ar", "hash", TipoPerfil.ADMINISTRADOR)
    docente = Usuario.crear("Ana", f"ana.{sufijo}@fiuner.edu.ar", "hash", TipoPerfil.DOCENTE)
    await usuarios.guardar(admin)
    await usuarios.guardar(docente)
    comision = Comision.crear(materia.id, "lu 10-12", admin.id)
    comisiones = SQLAlchemyComisionRepository(session)
    await comisiones.guardar(comision)
    comision.asignar_docente(docente.id)
    await comisiones.actualizar(comision)
    return Escenario(comision.id, docente.id, _headers(docente.id))


def _cliente() -> AsyncClient:
    return AsyncClient(transport=ASGITransport(app=app), base_url="http://test")


async def _generar(esc: Escenario, minutos: int | None = None) -> Response:
    cuerpo = {} if minutos is None else {"duracion_minutos": minutos}
    async with _cliente() as client:
        return await client.post(
            f"/comisiones/{esc.comision_id}/invitaciones-grupales", json=cuerpo, headers=esc.headers
        )


async def _ultima(esc: Escenario) -> Response:
    async with _cliente() as client:
        return await client.get(
            f"/comisiones/{esc.comision_id}/invitaciones-grupales/ultima", headers=esc.headers
        )


async def _revocar(esc: Escenario, invitacion_id: str, headers: dict[str, str] | None = None):
    async with _cliente() as client:
        return await client.post(
            f"/comisiones/{esc.comision_id}/invitaciones-grupales/{invitacion_id}/revocar",
            headers=headers or esc.headers,
        )


async def _registrar(token: str, numero: int, password: str = PASSWORD, email: str | None = None):
    async with _cliente() as client:
        return await client.post(
            "/identidad/registro",
            json={
                "token": token,
                "nombre": f"Estudiante {numero}",
                "email": email or f"est{numero}.{uuid.uuid4()}@fiuner.edu.ar",
                "password": password,
            },
        )


async def _preview(token: str) -> Response:
    async with _cliente() as client:
        return await client.get(f"/identidad/invitaciones/{token}")


async def _vencer(session, invitacion_id: str) -> None:
    await session.execute(
        update(InvitacionModel)
        .where(InvitacionModel.id == uuid.UUID(invitacion_id))
        .values(expira_en=datetime.now(UTC) - timedelta(minutes=1))
    )
    await session.commit()
