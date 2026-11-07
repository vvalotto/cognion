"""Ayudas compartidas de US-ADJ-63: medición del event loop y guarda de los casos de uso."""

from __future__ import annotations

import ast
import asyncio
import time
from collections.abc import Awaitable, Callable
from pathlib import Path

import bcrypt

# La versión que bloquea deja huecos de 250 a 325 ms con bcrypt costo 12; con hilos quedan en decenas.
UMBRAL_BLOQUEO = 0.150
INTENTOS = (
    3  # un CI cargado puede retrasar al azar un latido: se falla solo si lo hace 3 veces seguidas
)
PASSWORD = "Clave#Segura-2026"
HASH_PREVIO = bcrypt.hashpw(
    PASSWORD.encode(), bcrypt.gensalt()
).decode()  # sin pasar por el adaptador


async def hueco_maximo(trabajo: Callable[[], Awaitable[object]]) -> float:
    """Mayor tiempo entre dos latidos de 10 ms mientras corre `trabajo` (indica cuánto se congeló el loop)."""
    latidos: list[float] = []
    fin = asyncio.Event()

    async def latido() -> None:
        while not fin.is_set():
            latidos.append(time.perf_counter())
            await asyncio.sleep(0.010)

    tarea = asyncio.create_task(latido())
    await asyncio.sleep(0.05)  # deja que el latido arranque antes de medir
    await trabajo()
    latidos.append(
        time.perf_counter()
    )  # sin este último punto, un bloqueo hasta el final no deja huella
    fin.set()
    await tarea
    return max(b - a for a, b in zip(latidos, latidos[1:], strict=False))


async def sin_bloqueo(trabajo: Callable[[], Awaitable[object]]) -> float:
    """Devuelve el mejor hueco de hasta `INTENTOS` corridas (basta una para demostrar que no bloquea)."""
    mejor = float("inf")
    for _ in range(INTENTOS):
        mejor = min(mejor, await hueco_maximo(trabajo))
        if mejor < UMBRAL_BLOQUEO:
            break
    return mejor


RAIZ_SRC = Path(__file__).resolve().parents[3] / "src"

_METODOS_QUE_BLOQUEAN = {"hash", "verificar"}
_METODOS_ASINCRONOS = {"hash_async", "verificar_async"}


def llamadas_prohibidas_al_hasher(codigo: str) -> list[str]:
    """Llamadas al hasher que bloquean (`hash`/`verificar`) o que no esperan su resultado."""
    arbol = ast.parse(codigo)
    esperadas = {id(n.value) for n in ast.walk(arbol) if isinstance(n, ast.Await)}
    problemas: list[str] = []
    for nodo in ast.walk(arbol):
        if not (isinstance(nodo, ast.Call) and isinstance(nodo.func, ast.Attribute)):
            continue
        receptor = ast.unparse(nodo.func.value)
        if "hasher" not in receptor:
            continue
        if nodo.func.attr in _METODOS_QUE_BLOQUEAN:
            problemas.append(
                f"línea {nodo.lineno}: {receptor}.{nodo.func.attr}() bloquea el event loop"
            )
        elif nodo.func.attr in _METODOS_ASINCRONOS and id(nodo) not in esperadas:
            problemas.append(f"línea {nodo.lineno}: {receptor}.{nodo.func.attr}() sin await")
    return problemas
