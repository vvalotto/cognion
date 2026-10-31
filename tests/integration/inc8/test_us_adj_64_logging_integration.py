"""Logging real de `uvicorn` con `EMAIL_MODO=consola` y tokens enmascarados (US-ADJ-64).

Cada test arranca un `uvicorn src.app:app` en otro proceso y lee su salida real. Requiere una base
descartable (`DATABASE_URL` inline): estos tests vacían tablas.
"""

from __future__ import annotations

import uuid
from collections.abc import Iterator
from datetime import UTC, datetime, timedelta

import httpx
import pytest

from src.identidad.entities.usuario import Usuario
from src.identidad.frameworks.security.password_hasher import BcryptPasswordHasher
from src.identidad.interface_adapters.gateways.usuario_repository import SQLAlchemyUsuarioRepository
from src.shared.entities.tipo_perfil import TipoPerfil
from tests.integration.conftest import _id_desde_headers
from tests.integration.inc8._escenarios_logging import intentar_websocket, materia_y_comision
from tests.integration.inc8._servidor_real import ServidorReal


@pytest.fixture
def servidor() -> Iterator[ServidorReal]:
    """Servidor real en modo consola, detenido al terminar el test."""
    real = ServidorReal(EMAIL_MODO="consola", ENTORNO="desarrollo", LOG_LEVEL="INFO")
    real.iniciar()
    yield real
    real.detener()


# ---------------------------------------------------------------- emails de consola


async def test_recuperar_password_deja_el_email_y_el_link_en_la_salida_real(
    servidor: ServidorReal, session
) -> None:
    """Escenario 1 (hallazgo #2): el email de consola aparece en la salida del proceso real."""
    email = f"docente.{uuid.uuid4()}@fiuner.edu.ar"
    await SQLAlchemyUsuarioRepository(session).guardar(
        Usuario.crear("Docente", email, BcryptPasswordHasher().hash("x"), TipoPerfil.DOCENTE)
    )

    async with httpx.AsyncClient(base_url=servidor.url) as client:
        respuesta = await client.post(
            "/identidad/recuperar-password/solicitar", json={"email": email}
        )
    assert respuesta.status_code == 202

    salida = servidor.esperar_en_salida("/recuperar-password/")
    assert "Email (modo consola)" in salida
    assert email in salida
    assert "/recuperar-password/" in salida


async def test_invitacion_con_email_deja_el_token_en_la_salida(
    servidor: ServidorReal, session, admin_headers, docente_headers
) -> None:
    """Escenario 2: el token de la invitación (el email trae el token suelto, no un link) se ve en el log."""
    _, comision_id, _ = await materia_y_comision(servidor, session, admin_headers, docente_headers)
    docente_id = str(_id_desde_headers(docente_headers))

    async with httpx.AsyncClient(base_url=servidor.url) as client:
        respuesta = await client.post(
            f"/comisiones/{comision_id}/invitaciones",
            json={"docente_id": docente_id, "email_destinatario": "alumno@fiuner.edu.ar"},
            headers=docente_headers,
        )
    assert respuesta.status_code == 201
    token = respuesta.json()["token"]

    salida = servidor.esperar_en_salida("alumno@fiuner.edu.ar")
    assert "Email (modo consola)" in salida
    assert (
        f"Token de invitación: {token}" in salida
    )  # el cuerpo del email conserva el token completo


async def test_aviso_de_apertura_de_actividad_aparece_en_la_salida(
    servidor: ServidorReal, session, admin_headers, docente_headers
) -> None:
    """Escenario 3: el aviso de apertura (RF-14) dirigido al estudiante se ve en el log."""
    materia_id, comision_id, emails = await materia_y_comision(
        servidor, session, admin_headers, docente_headers, estudiantes=1
    )
    async with httpx.AsyncClient(base_url=servidor.url) as client:
        banco_id = (await client.get("/materias", headers=docente_headers)).json()
        banco_id = next(m["banco_id"] for m in banco_id if m["id"] == materia_id)
        for i in range(3):
            await client.post(
                "/preguntas/verdadero-falso",
                json={
                    "banco_id": banco_id,
                    "texto": f"Pregunta {i}",
                    "respuesta_correcta": True,
                    "unidad_tematica": "U",
                    "tema": "T",
                    "dificultad": "medio",
                    "importancia": "alto",
                },
                headers=docente_headers,
            )
        apertura = datetime.now(UTC)
        creada = await client.post(
            "/actividades",
            json={
                "materia_id": materia_id,
                "fecha_apertura": apertura.isoformat(),
                "fecha_cierre": (apertura + timedelta(days=7)).isoformat(),
                "cantidad_preguntas": 2,
                "cantidad_intentos_permitidos": 1,
                "titulo": "Parcial de prueba",
                "comisiones_ids": [comision_id],
            },
            headers=docente_headers,
        )
    assert creada.status_code == 201

    salida = servidor.esperar_en_salida(emails[0])
    assert "Email (modo consola)" in salida
    assert emails[0] in salida


# ---------------------------------------------------------------- tokens enmascarados


async def test_el_jwt_del_canal_en_vivo_no_queda_en_la_salida(
    servidor: ServidorReal, docente_headers
) -> None:
    """Escenario 4 (hallazgo #9): la línea del WebSocket dice `token=***`, el JWT no aparece."""
    jwt = docente_headers["Authorization"].removeprefix("Bearer ")
    await intentar_websocket(servidor, str(uuid.uuid4()), jwt)

    salida = servidor.esperar_en_salida("token=***")
    assert "WebSocket" in salida and "token=***" in salida
    assert jwt not in salida


async def test_la_invitacion_no_queda_en_el_log_de_acceso(
    servidor: ServidorReal, session, admin_headers, docente_headers
) -> None:
    """Escenario 5: `GET /registro?token=…` se registra con `token=***`."""
    _, comision_id, _ = await materia_y_comision(servidor, session, admin_headers, docente_headers)
    async with httpx.AsyncClient(base_url=servidor.url) as client:
        invitacion = await client.post(
            f"/comisiones/{comision_id}/invitaciones",
            json={"docente_id": str(_id_desde_headers(docente_headers))},
            headers=docente_headers,
        )
        token = invitacion.json()["token"]
        await client.get(f"/registro?token={token}")

    salida = servidor.esperar_en_salida("GET /registro?token=***")
    assert "GET /registro?token=***" in salida
    assert token not in salida


async def test_un_token_invalido_tampoco_queda_escrito(servidor: ServidorReal) -> None:
    """Escenario 6: la línea de rechazo no contiene el valor del token."""
    await intentar_websocket(servidor, str(uuid.uuid4()), "token-invalido-secreto-123")

    salida = servidor.esperar_en_salida("token=***")
    assert "token=***" in salida
    assert "token-invalido-secreto-123" not in salida


async def test_el_link_de_recuperacion_abierto_no_queda_en_el_log_de_acceso(
    servidor: ServidorReal,
) -> None:
    """Extensión de la spec: `GET /recuperar-password/<token>` se registra con `***`."""
    token = "ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789abc"
    async with httpx.AsyncClient(base_url=servidor.url) as client:
        await client.get(f"/recuperar-password/{token}")

    salida = servidor.esperar_en_salida("/recuperar-password/***")
    assert "GET /recuperar-password/***" in salida
    assert token not in salida


# ---------------------------------------------------------------- lo demás no cambia


async def test_el_health_check_mantiene_el_formato_de_uvicorn(servidor: ServidorReal) -> None:
    """Escenario 7: las demás líneas de `uvicorn` no cambian."""
    async with httpx.AsyncClient(base_url=servidor.url) as client:
        await client.get("/health")
    salida = servidor.esperar_en_salida('"GET /health HTTP/1.1" 200 OK')
    assert "INFO:     127.0.0.1:" in salida
    assert '"GET /health HTTP/1.1" 200 OK' in salida
    assert "***" not in salida.split("Application startup complete")[0]
