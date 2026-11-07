"""El hash de contraseñas no bloquea el event loop (US-ADJ-63).

Usa el hasher real (bcrypt, costo 12): el bloqueo es una propiedad de bcrypt verdadero. No toca la base.
"""

from __future__ import annotations

import asyncio

import pytest

from src.identidad.entities.ports.password_hasher_port import PasswordHasherPort
from src.identidad.frameworks.security.password_hasher import BcryptPasswordHasher
from tests.unit.inc1._fakes import FakePasswordHasher
from tests.unit.inc9._hasher_async_comun import (
    HASH_PREVIO,
    PASSWORD,
    RAIZ_SRC,
    UMBRAL_BLOQUEO,
    llamadas_prohibidas_al_hasher,
    sin_bloqueo,
)

# ----------------------------------------------------------------------- event loop libre


async def test_verificar_tres_contrasenas_a_la_vez_no_congela_el_event_loop() -> None:
    """Escenario 1: el hueco máximo queda bajo el umbral y las 3 verificaciones son correctas."""
    hasher = BcryptPasswordHasher()
    resultados: list[bool] = []

    async def trabajo() -> None:
        resultados[:] = await asyncio.gather(
            *(hasher.verificar_async(PASSWORD, HASH_PREVIO) for _ in range(3))
        )

    hueco = await sin_bloqueo(trabajo)
    assert hueco < UMBRAL_BLOQUEO, f"el event loop quedó {hueco:.3f} s sin responder"
    assert resultados == [True, True, True]


async def test_calcular_tres_hashes_a_la_vez_no_congela_el_event_loop() -> None:
    """Escenario 2: lo mismo con `hash`; cada hash verifica contra su contraseña original."""
    hasher = BcryptPasswordHasher()
    hashes: list[str] = []

    async def trabajo() -> None:
        hashes[:] = await asyncio.gather(*(hasher.hash_async(f"{PASSWORD}-{i}") for i in range(3)))

    hueco = await sin_bloqueo(trabajo)
    assert hueco < UMBRAL_BLOQUEO, f"el event loop quedó {hueco:.3f} s sin responder"
    assert all(hasher.verificar(f"{PASSWORD}-{i}", h) for i, h in enumerate(hashes))


# ----------------------------------------------------------------------- compatibilidad


async def test_un_hash_generado_antes_del_cambio_se_verifica_despues() -> None:
    """Escenario 3: compatibilidad con los hashes ya guardados en la base."""
    hasher = BcryptPasswordHasher()
    assert await hasher.verificar_async(PASSWORD, HASH_PREVIO) is True
    assert await hasher.verificar_async("otra-contraseña", HASH_PREVIO) is False


async def test_el_hash_nuevo_conserva_el_algoritmo_y_el_costo() -> None:
    """Escenario 4: formato bcrypt `$2b$12$`, y verifica tanto en la forma asíncrona como en la síncrona."""
    hasher = BcryptPasswordHasher()
    nuevo = await hasher.hash_async(PASSWORD)
    assert nuevo.startswith("$2b$12$")
    assert await hasher.verificar_async(PASSWORD, nuevo) is True
    assert hasher.verificar(PASSWORD, nuevo) is True


async def test_la_forma_asincrona_da_el_mismo_resultado_que_la_sincrona() -> None:
    """Misma salida con y sin hilo."""
    hasher = BcryptPasswordHasher()
    for password, esperado in ((PASSWORD, True), ("incorrecta", False)):
        assert await hasher.verificar_async(password, HASH_PREVIO) is esperado
        assert hasher.verificar(password, HASH_PREVIO) is esperado


# ----------------------------------------------------------------------- puerto y fake


def test_el_puerto_exige_las_formas_asincronas() -> None:
    """Un hasher sin `hash_async`/`verificar_async` no se puede instanciar."""

    class Incompleto(PasswordHasherPort):
        def hash(self, password: str) -> str:
            return password

        def verificar(self, password: str, password_hash: str) -> bool:
            return True

    with pytest.raises(TypeError):
        Incompleto()  # type: ignore[abstract]


async def test_el_fake_implementa_las_formas_asincronas() -> None:
    """Los tests de casos de uso usan el fake sin bcrypt."""
    fake = FakePasswordHasher()
    assert await fake.hash_async("x") == "hashed:x"
    assert await fake.verificar_async("x", "hashed:x") is True
    assert await fake.verificar_async("y", "hashed:x") is False


# ----------------------------------------------------------------------- guarda de los casos de uso


def test_la_guarda_detecta_las_llamadas_que_bloquean_o_sin_await() -> None:
    """La guarda no es decorativa: marca las dos formas incorrectas y acepta la correcta."""
    mal_sincrona = "async def f(self):\n    return self._hasher.verificar('a', 'b')\n"
    mal_sin_await = "async def f(self):\n    return self._hasher.hash_async('a')\n"
    bien = "async def f(self):\n    return await self._hasher.hash_async('a')\n"
    assert llamadas_prohibidas_al_hasher(mal_sincrona) != []
    assert llamadas_prohibidas_al_hasher(mal_sin_await) != []
    assert llamadas_prohibidas_al_hasher(bien) == []


def test_ningun_caso_de_uso_llama_al_hasher_en_forma_que_bloquee() -> None:
    """Escenario 6: recorre el código real de todos los casos de uso de `src/`."""
    problemas: list[str] = []
    archivos = sorted(RAIZ_SRC.glob("*/use_cases/*.py"))
    assert archivos, "no se encontraron casos de uso: la guarda no está revisando nada"
    for archivo in archivos:
        problemas += [
            f"{archivo.relative_to(RAIZ_SRC.parent)}: {p}"
            for p in llamadas_prohibidas_al_hasher(archivo.read_text(encoding="utf-8"))
        ]
    assert problemas == []
