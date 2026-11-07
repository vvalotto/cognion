"""Steps BDD de US-ADJ-63 — El hash de contraseñas no bloquea el event loop.

Usan el hasher bcrypt real (el bloqueo es una propiedad de bcrypt verdadero) y no tocan la base.
"""

from __future__ import annotations

import asyncio
from typing import Any
from uuid import uuid4

import pytest
from pytest_bdd import given, scenarios, then, when

from src.identidad.entities.errors import CredencialesInvalidas
from src.identidad.entities.usuario import Usuario
from src.identidad.frameworks.security.password_hasher import BcryptPasswordHasher
from src.identidad.use_cases.iniciar_sesion import IniciarSesionUseCase
from tests.unit.inc1._fakes import FakeJWTIssuer, FakeUsuarioRepository
from tests.unit.inc9._hasher_async_comun import (
    HASH_PREVIO,
    PASSWORD,
    RAIZ_SRC,
    UMBRAL_BLOQUEO,
    llamadas_prohibidas_al_hasher,
    sin_bloqueo,
)

scenarios("../../features/inc9/US-ADJ-63-hash-no-bloquea.feature")


def run_async(coro):
    """pytest-bdd no soporta step functions async def — ver ADR-018."""
    return asyncio.run(coro)


@pytest.fixture
def ctx() -> dict[str, Any]:
    """Estado compartido entre los steps de un escenario."""
    return {"hasher": BcryptPasswordHasher()}


# ---------------------------------------------------------------- Given


@given("una tarea que registra el paso del tiempo cada 10 milisegundos")
def tarea_de_latidos(ctx: dict[str, Any]) -> None:
    """La medición del event loop se arma dentro de `sin_bloqueo` al correr el trabajo."""
    ctx["medir"] = True


@given("un hash bcrypt generado con la implementación anterior")
def hash_anterior(ctx: dict[str, Any]) -> None:
    """Un hash hecho con `bcrypt.hashpw` directo, sin pasar por el adaptador nuevo."""
    ctx["hash_previo"] = HASH_PREVIO


@given("un Estudiante con una contraseña conocida")
def estudiante_con_password(ctx: dict[str, Any]) -> None:
    """Un Estudiante en un repositorio en memoria, con su contraseña hasheada con bcrypt real."""
    repo = FakeUsuarioRepository()
    estudiante = Usuario.crear_estudiante(
        "Estudiante",
        "estudiante@fiuner.edu.ar",
        ctx["hasher"].hash(PASSWORD),
        uuid4(),
    )
    repo.usuarios[estudiante.id] = estudiante
    ctx["repo"] = repo


@given("el código de los casos de uso de Identidad")
def codigo_de_los_casos_de_uso(ctx: dict[str, Any]) -> None:
    """Los archivos de los casos de uso de todos los BC."""
    ctx["archivos"] = sorted(RAIZ_SRC.glob("*/use_cases/*.py"))
    assert ctx["archivos"]


# ---------------------------------------------------------------- When


@when("se verifican 3 contraseñas a la vez con el hasher real")
def verificar_tres(ctx: dict[str, Any]) -> None:
    """Tres `verificar_async` simultáneos mientras el latido mide el event loop."""

    async def medir() -> None:
        async def trabajo() -> None:
            ctx["resultados"] = await asyncio.gather(
                *(ctx["hasher"].verificar_async(PASSWORD, HASH_PREVIO) for _ in range(3))
            )

        ctx["hueco"] = await sin_bloqueo(trabajo)

    run_async(medir())


@when("se calculan 3 hashes a la vez con el hasher real")
def hashear_tres(ctx: dict[str, Any]) -> None:
    """Tres `hash_async` simultáneos mientras el latido mide el event loop."""

    async def medir() -> None:
        async def trabajo() -> None:
            ctx["hashes"] = await asyncio.gather(
                *(ctx["hasher"].hash_async(f"{PASSWORD}-{i}") for i in range(3))
            )

        ctx["hueco"] = await sin_bloqueo(trabajo)

    run_async(medir())


@when("se verifica la contraseña original con el hasher nuevo")
def verificar_hash_anterior(ctx: dict[str, Any]) -> None:
    """Verifica el hash anterior con la contraseña correcta y con otra."""
    ctx["correcta"] = run_async(ctx["hasher"].verificar_async(PASSWORD, ctx["hash_previo"]))
    ctx["distinta"] = run_async(ctx["hasher"].verificar_async("otra", ctx["hash_previo"]))


@when("se calcula el hash de una contraseña con el hasher nuevo")
def calcular_hash_nuevo(ctx: dict[str, Any]) -> None:
    """Un hash nuevo por la forma asíncrona."""
    ctx["hash_nuevo"] = run_async(ctx["hasher"].hash_async(PASSWORD))


@when("inicia sesión con la contraseña correcta y con una incorrecta")
def iniciar_sesion(ctx: dict[str, Any]) -> None:
    """Login con el caso de uso real y el hasher real."""
    caso = IniciarSesionUseCase(ctx["repo"], ctx["hasher"], FakeJWTIssuer())
    ctx["token"] = run_async(caso.execute("estudiante@fiuner.edu.ar", PASSWORD))

    async def incorrecta() -> None:
        with pytest.raises(CredencialesInvalidas):
            await caso.execute("estudiante@fiuner.edu.ar", "incorrecta")

    run_async(incorrecta())


@when("se revisan las llamadas al hasher")
def revisar_llamadas(ctx: dict[str, Any]) -> None:
    """Aplica la guarda a cada archivo de casos de uso."""
    ctx["problemas"] = [
        f"{archivo.name}: {problema}"
        for archivo in ctx["archivos"]
        for problema in llamadas_prohibidas_al_hasher(archivo.read_text(encoding="utf-8"))
    ]


# ---------------------------------------------------------------- Then


@then("el mayor hueco entre dos registros de tiempo es menor al umbral de bloqueo")
def hueco_chico(ctx: dict[str, Any]) -> None:
    """El event loop siguió respondiendo durante el trabajo."""
    assert ctx["hueco"] < UMBRAL_BLOQUEO, f"el event loop quedó {ctx['hueco']:.3f} s sin responder"


@then("las 3 verificaciones dan el resultado correcto")
def tres_verificaciones_correctas(ctx: dict[str, Any]) -> None:
    """Las tres verificaciones dieron `True`."""
    assert list(ctx["resultados"]) == [True, True, True]


@then("cada hash verifica contra su contraseña original")
def cada_hash_verifica(ctx: dict[str, Any]) -> None:
    """Cada hash calculado en paralelo corresponde a su contraseña."""
    assert all(ctx["hasher"].verificar(f"{PASSWORD}-{i}", h) for i, h in enumerate(ctx["hashes"]))


@then("la verificación es correcta")
def verificacion_correcta(ctx: dict[str, Any]) -> None:
    """El hash anterior se verifica con el hasher nuevo."""
    assert ctx["correcta"] is True


@then("una contraseña distinta es rechazada")
def distinta_rechazada(ctx: dict[str, Any]) -> None:
    """Otra contraseña no verifica."""
    assert ctx["distinta"] is False


@then("el hash tiene el formato bcrypt con costo 12")
def formato_bcrypt(ctx: dict[str, Any]) -> None:
    """Prefijo `$2b$12$` y verificación correcta."""
    assert ctx["hash_nuevo"].startswith("$2b$12$")
    assert ctx["hasher"].verificar(PASSWORD, ctx["hash_nuevo"])


@then("la correcta entrega un token y la incorrecta es rechazada")
def token_y_rechazo(ctx: dict[str, Any]) -> None:
    """El login correcto devolvió un token; el incorrecto levantó `CredencialesInvalidas`."""
    jwt, _evento = ctx["token"]
    assert jwt.token


@then("todas esperan el resultado y ninguna usa la forma que bloquea")
def todas_esperan(ctx: dict[str, Any]) -> None:
    """La guarda no encontró llamadas prohibidas."""
    assert ctx["problemas"] == []
