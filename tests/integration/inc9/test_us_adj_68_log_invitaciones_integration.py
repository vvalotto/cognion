"""El `uvicorn` real no escribe el token de las invitaciones en el log de acceso (US-ADJ-68).

Cada test arranca un `uvicorn src.app:app` en otro proceso y lee su salida real (`caplog` no alcanza,
`US-ADJ-64`). Requiere una base descartable (`DATABASE_URL` inline): estos tests vacían tablas.
"""

from __future__ import annotations

import secrets
from collections.abc import Iterator

import httpx
import pytest

from tests.integration.conftest import _id_desde_headers
from tests.integration.inc8._escenarios_logging import materia_y_comision
from tests.integration.inc8._servidor_real import ServidorReal


@pytest.fixture
def servidor() -> Iterator[ServidorReal]:
    """Servidor real, detenido al terminar el test."""
    real = ServidorReal(EMAIL_MODO="consola", ENTORNO="desarrollo", LOG_LEVEL="INFO")
    real.iniciar()
    yield real
    real.detener()


async def _invitacion_vigente(
    servidor: ServidorReal, session, admin_headers, docente_headers
) -> tuple[str, str]:
    """Crea una invitación por la API real y devuelve `(comision_id, token)`."""
    _, comision_id, _ = await materia_y_comision(servidor, session, admin_headers, docente_headers)
    async with httpx.AsyncClient(base_url=servidor.url) as client:
        creada = await client.post(
            f"/comisiones/{comision_id}/invitaciones",
            json={"docente_id": str(_id_desde_headers(docente_headers))},
            headers=docente_headers,
        )
    assert creada.status_code == 201
    return comision_id, creada.json()["token"]


async def test_consultar_una_invitacion_vigente_no_deja_el_token_en_el_log(
    servidor: ServidorReal, session, admin_headers, docente_headers
) -> None:
    """Escenarios 1 y 3: ruta enmascarada, token ausente, método y estado a la vista."""
    _, token = await _invitacion_vigente(servidor, session, admin_headers, docente_headers)
    async with httpx.AsyncClient(base_url=servidor.url) as client:
        respuesta = await client.get(f"/identidad/invitaciones/{token}")
    assert respuesta.status_code == 200

    salida = servidor.esperar_en_salida('GET /identidad/invitaciones/*** HTTP/1.1" 200')
    assert 'GET /identidad/invitaciones/*** HTTP/1.1" 200' in salida
    assert token not in salida


async def test_un_token_que_no_corresponde_a_una_invitacion_tampoco_queda_en_el_log(
    servidor: ServidorReal,
) -> None:
    """Escenario 2: un token inexistente (404) tampoco queda escrito."""
    inexistente = secrets.token_urlsafe(32)
    async with httpx.AsyncClient(base_url=servidor.url) as client:
        respuesta = await client.get(f"/identidad/invitaciones/{inexistente}")
    assert respuesta.status_code == 404

    salida = servidor.esperar_en_salida('GET /identidad/invitaciones/*** HTTP/1.1" 404')
    assert 'GET /identidad/invitaciones/*** HTTP/1.1" 404' in salida
    assert inexistente not in salida


async def test_una_invitacion_ya_usada_responde_422_y_no_deja_el_token(
    servidor: ServidorReal, session, admin_headers, docente_headers
) -> None:
    """Escenario 2 (variante): el caso real de la prueba del 2026-11-06, el link ya usado."""
    comision_id, token = await _invitacion_vigente(
        servidor, session, admin_headers, docente_headers
    )
    async with httpx.AsyncClient(base_url=servidor.url) as client:
        registro = await client.post(
            "/identidad/registro",
            json={
                "token": token,
                "nombre": "Estudiante Uno",
                "email": f"uno.{secrets.token_hex(4)}@fiuner.edu.ar",
                "password": "Clave#Segura-2026",
            },
        )
        assert registro.status_code == 201, registro.text
        usada = await client.get(f"/identidad/invitaciones/{token}")
    assert usada.status_code == 422

    salida = servidor.esperar_en_salida('GET /identidad/invitaciones/*** HTTP/1.1" 422')
    assert 'GET /identidad/invitaciones/*** HTTP/1.1" 422' in salida
    assert token not in salida
    assert comision_id  # la comisión existía: el rechazo fue por el estado de la invitación


async def test_generar_una_invitacion_se_registra_sin_enmascarar(
    servidor: ServidorReal, session, admin_headers, docente_headers
) -> None:
    """Escenario 4: `POST /comisiones/<id>/invitaciones` queda tal cual."""
    comision_id, _ = await _invitacion_vigente(servidor, session, admin_headers, docente_headers)

    salida = servidor.esperar_en_salida(
        f'POST /comisiones/{comision_id}/invitaciones HTTP/1.1" 201'
    )
    assert f'POST /comisiones/{comision_id}/invitaciones HTTP/1.1" 201' in salida
    assert "invitaciones/***" not in salida.split("POST /comisiones/")[1].split("\n")[0]


async def test_el_enlace_de_registro_sigue_enmascarado(
    servidor: ServidorReal, session, admin_headers, docente_headers
) -> None:
    """Escenario 5: `token=` en la query sigue funcionando como en `US-ADJ-64`."""
    _, token = await _invitacion_vigente(servidor, session, admin_headers, docente_headers)
    async with httpx.AsyncClient(base_url=servidor.url) as client:
        await client.get(f"/registro?token={token}")

    salida = servidor.esperar_en_salida("GET /registro?token=***")
    assert "GET /registro?token=***" in salida
    assert token not in salida
