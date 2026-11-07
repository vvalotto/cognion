"""Un `uvicorn` real sigue respondiendo mientras varias personas inician sesión (US-ADJ-63).

Reproduce el hallazgo de la prueba en GCP: con bcrypt en el hilo del event loop, cada verificación
congelaba la aplicación entera. Requiere una base descartable (`DATABASE_URL` inline): estos tests
vacían tablas.
"""

from __future__ import annotations

import asyncio
import time
import uuid
from collections.abc import Iterator

import httpx
import pytest

from src.identidad.entities.usuario import Usuario
from src.identidad.frameworks.security.password_hasher import BcryptPasswordHasher
from src.identidad.interface_adapters.gateways.usuario_repository import SQLAlchemyUsuarioRepository
from src.shared.entities.tipo_perfil import TipoPerfil
from tests.integration.inc8._servidor_real import ServidorReal

PASSWORD = "Clave#Segura-2026"
# Bloqueado, `/health` espera lo que tarde bcrypt (300 a 400 ms o más, en serie); libre, responde en decenas.
UMBRAL_LATENCIA = 0.35


@pytest.fixture
def servidor() -> Iterator[ServidorReal]:
    """Servidor real, detenido al terminar el test."""
    real = ServidorReal(EMAIL_MODO="consola", ENTORNO="desarrollo", LOG_LEVEL="INFO")
    real.iniciar()
    yield real
    real.detener()


async def _crear_docente(session) -> str:
    email = f"docente.{uuid.uuid4()}@fiuner.edu.ar"
    await SQLAlchemyUsuarioRepository(session).guardar(
        Usuario.crear("Docente", email, BcryptPasswordHasher().hash(PASSWORD), TipoPerfil.DOCENTE)
    )
    return email


async def _latencia_maxima_de_health_durante(
    servidor: ServidorReal, logins: list[dict[str, str]]
) -> tuple[float, list[int]]:
    """Dispara los logins a la vez y mide cuánto tarda `/health` mientras tanto."""
    latencias: list[float] = []
    terminaron = asyncio.Event()

    async with httpx.AsyncClient(base_url=servidor.url, timeout=30) as cliente:

        async def sondear() -> None:
            while not terminaron.is_set():
                inicio = time.perf_counter()
                await cliente.get("/health")
                latencias.append(time.perf_counter() - inicio)
                await asyncio.sleep(0.02)

        sonda = asyncio.create_task(sondear())
        await asyncio.sleep(0.2)  # primeras mediciones sin carga
        respuestas = await asyncio.gather(
            *(cliente.post("/identidad/login", json=cuerpo) for cuerpo in logins)
        )
        terminaron.set()
        await sonda
    return max(latencias), [r.status_code for r in respuestas]


async def test_health_responde_mientras_tres_personas_inician_sesion(
    servidor: ServidorReal, session
) -> None:
    """Tres logins simultáneos (correctos) no dejan sin respuesta al resto de la aplicación."""
    email = await _crear_docente(session)
    logins = [{"email": email, "password": PASSWORD}] * 3

    peor, estados = await _latencia_maxima_de_health_durante(servidor, logins)

    assert estados == [200, 200, 200]
    assert peor < UMBRAL_LATENCIA, f"/health tardó {peor:.3f} s durante los logins"


async def test_logins_correctos_e_incorrectos_se_comportan_igual(
    servidor: ServidorReal, session
) -> None:
    """El comportamiento funcional no cambia: la correcta entra, la incorrecta es rechazada."""
    email = await _crear_docente(session)
    logins = [
        {"email": email, "password": PASSWORD},
        {"email": email, "password": "incorrecta"},
    ]

    _, estados = await _latencia_maxima_de_health_durante(servidor, logins)

    assert estados == [200, 401]
