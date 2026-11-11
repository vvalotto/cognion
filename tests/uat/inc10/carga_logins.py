"""UAT (US-10.1.1): 30 logins simultáneos y la latencia de /health mientras tanto (efecto de US-ADJ-63).

Con el hash de contraseñas bloqueando el event loop, /health tardaba lo que dura la ráfaga; con `hash_async` debe
seguir respondiendo en milisegundos. Uso: UAT_URL=... UAT_EMAIL=... UAT_PASSWORD=... python carga_logins.py
"""

from __future__ import annotations

import asyncio
import os
import statistics
import time

import httpx

URL = os.environ.get("UAT_URL", "http://localhost:8010").rstrip("/") + "/api"
N = int(os.environ.get("UAT_N", "30"))


async def login(c: httpx.AsyncClient) -> float:
    """Un login; devuelve cuánto tardó."""
    t = time.perf_counter()
    r = await c.post(
        "/identidad/login",
        json={"email": os.environ["UAT_EMAIL"], "password": os.environ["UAT_PASSWORD"]},
    )
    assert r.status_code == 200, r.status_code
    return time.perf_counter() - t


async def sondear(c: httpx.AsyncClient, parar: asyncio.Event) -> list[float]:
    """Mide /health cada 20 ms hasta que termina la ráfaga."""
    tiempos: list[float] = []
    while not parar.is_set():
        t = time.perf_counter()
        r = await c.get("/health")
        assert r.status_code == 200
        tiempos.append(time.perf_counter() - t)
        await asyncio.sleep(0.02)
    return tiempos


async def main() -> None:
    """Dispara N logins a la vez y reporta tiempos."""
    async with httpx.AsyncClient(
        base_url=URL, timeout=60, limits=httpx.Limits(max_connections=N + 5)
    ) as c:
        reposo = []
        for _ in range(10):
            t = time.perf_counter()
            await c.get("/health")
            reposo.append(time.perf_counter() - t)
        parar = asyncio.Event()
        sonda = asyncio.create_task(sondear(c, parar))
        inicio = time.perf_counter()
        tiempos = await asyncio.gather(*[login(c) for _ in range(N)])
        total = time.perf_counter() - inicio
        parar.set()
        health = await sonda
    ms = lambda x: round(x * 1000)  # noqa: E731
    print(
        f"{N} logins simultáneos OK en {total:.2f} s (login: mediana {ms(statistics.median(tiempos))} ms, máx {ms(max(tiempos))} ms)"
    )
    print(f"/health en reposo: mediana {ms(statistics.median(reposo))} ms")
    print(
        f"/health DURANTE la ráfaga: {len(health)} consultas, mediana {ms(statistics.median(health))} ms, máx {ms(max(health))} ms"
    )


asyncio.run(main())
