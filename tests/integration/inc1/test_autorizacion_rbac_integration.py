import uuid
from datetime import UTC, datetime, timedelta

import jwt as pyjwt
from httpx import ASGITransport, AsyncClient

from src.app import app
from src.identidad.entities.usuario import TipoPerfil
from src.identidad.frameworks.security.jwt_pyjwt import PyJWTIssuer
from src.settings import settings


def _headers(rol: TipoPerfil) -> dict[str, str]:
    jwt_vo = PyJWTIssuer().emitir(uuid.uuid4(), rol)
    return {"Authorization": f"Bearer {jwt_vo.token}"}


def _headers_expirado(rol: TipoPerfil) -> dict[str, str]:
    payload = {
        "sub": str(uuid.uuid4()),
        "rol": rol.value,
        "exp": datetime.now(UTC) - timedelta(minutes=1),
    }
    token = pyjwt.encode(payload, settings.secret_key, algorithm=settings.algorithm)
    return {"Authorization": f"Bearer {token}"}


def _body_crear_usuario() -> dict[str, str]:
    return {
        "nombre": "Usuario de Test",
        "email": f"rbac.{uuid.uuid4()}@fiuner.edu.ar",
        "password": "Password#2026",
        "perfil": "docente",
    }


class TestAutorizacionRBACIntegration:
    """Escenarios de `tests/features/inc1/US-1.1.5-autorizacion-rbac.feature` (RF-02).

    Validados contra los endpoints de Identidad disponibles en este incremento
    (`usuarios`, `comisiones/{id}/invitaciones`) — no contra banco de preguntas ni
    analytics, todavía fuera de alcance (ver notas de implementación de la spec).
    """

    async def test_acceso_concedido_con_rol_suficiente(self):
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.post(
                "/usuarios", json=_body_crear_usuario(), headers=_headers(TipoPerfil.ADMINISTRADOR)
            )

        assert response.status_code == 201

    async def test_estudiante_rechazado_en_administracion_de_cuentas(self):
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.post(
                "/usuarios", json=_body_crear_usuario(), headers=_headers(TipoPerfil.ESTUDIANTE)
            )

        assert response.status_code == 403

    async def test_estudiante_rechazado_en_generacion_de_invitaciones(self):
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.post(
                f"/comisiones/{uuid.uuid4()}/invitaciones",
                json={"docente_id": str(uuid.uuid4()), "email_destinatario": "x@fiuner.edu.ar"},
                headers=_headers(TipoPerfil.ESTUDIANTE),
            )

        assert response.status_code == 403

    async def test_docente_rechazado_en_administracion_de_cuentas(self):
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.post(
                "/usuarios", json=_body_crear_usuario(), headers=_headers(TipoPerfil.DOCENTE)
            )

        assert response.status_code == 403

    async def test_request_sin_jwt_responde_401(self):
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.post("/usuarios", json=_body_crear_usuario())

        assert response.status_code == 401

    async def test_jwt_expirado_responde_401(self):
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.post(
                "/usuarios",
                json=_body_crear_usuario(),
                headers=_headers_expirado(TipoPerfil.ADMINISTRADOR),
            )

        assert response.status_code == 401
