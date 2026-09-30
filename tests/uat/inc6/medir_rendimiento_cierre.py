"""Medición reproducible del RNF de rendimiento del cierre de pregunta (US-6.2.9).

RNF (`RNF_v1.md`, Rendimiento, Escenario 1): procesamiento server-side <= 100 ms para transmitir
el resultado a una clase de 60 participantes. Este script mide `CerrarPreguntaActual` con 60
Estudiantes que ya respondieron, PostgreSQL real y 60 conexiones simuladas en el
`ConnectionManager` real (se mide el envío de 60 mensajes, no la red).

Criterio (lo que dice la spec): tiempo del use case, desde que empieza hasta que terminó de
publicar, sobre >= 30 repeticiones, con p95 <= 100 ms. Como medición complementaria (NO decide el
veredicto) se mide el mismo cierre por `POST /cerrar-pregunta` vía ASGI: suma JWT, wiring y la
conexión nueva a la DB por operación (`NullPool`, `ADR-017`).

Uso (desde la raíz del repo, con Postgres corriendo):

    PYTHONPATH=. .venv/bin/python tests/uat/inc6/medir_rendimiento_cierre.py

ATENCIÓN: vacía la DB local antes y después (mismo criterio que la suite de tests). Corre en la
máquina de desarrollo, no en producción: los números son una cota de referencia, no una garantía
del despliegue final.

Re-usado por `US-6.3.1` para re-medir el RNF tras sumar la resolución de nombres (una consulta
por lote más al camino de `CerrarPreguntaActual`) — mismo script, sin cambios de metodología.
"""

from __future__ import annotations

import asyncio
import json
import math
import platform
import statistics
import sys
import time
import uuid
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from httpx import ASGITransport, AsyncClient
from sqlalchemy import text

from src.actividad_evaluativa.frameworks.adapters.estudiante_consulta_port_in_process import (
    EstudianteConsultaPortInProcess,
)
from src.actividad_evaluativa.frameworks.adapters.pregunta_consulta_port_in_process import (
    PreguntaConsultaPortInProcess,
)
from src.actividad_evaluativa.frameworks.adapters.proyecciones_en_vivo_repository import (
    SQLAlchemyProyeccionesEnVivoQuery,
)
from src.actividad_evaluativa.frameworks.dependencies import get_connection_manager
from src.actividad_evaluativa.frameworks.event_store.sqlalchemy_event_store import (
    SQLAlchemyEventStore,
)
from src.actividad_evaluativa.frameworks.websockets.websocket_canal_tiempo_real import (
    WebSocketCanalTiempoReal,
)
from src.actividad_evaluativa.use_cases.cerrar_pregunta_actual import CerrarPreguntaActualUseCase
from src.app import app
from src.shared.entities.tipo_perfil import TipoPerfil
from src.shared.frameworks.db import SessionLocal
from tests.integration.inc6._helpers import (
    crear_estudiantes,
    headers_de,
    iniciar_sesion,
    preparar_sesion,
)

PARTICIPANTES = 60
SESIONES = 6  # 6 sesiones x 5 preguntas = 30 cierres sobre preguntas distintas
PREGUNTAS_POR_SESION = 5
UMBRAL_MS = 100.0
EVIDENCIA = Path("quality/reports/uat/inc6/rendimiento-cierre.json")


class ConexionSimulada:
    """WebSocket en memoria: acepta y cuenta los mensajes recibidos (sin red)."""

    def __init__(self) -> None:
        """Arranca sin mensajes recibidos."""
        self.recibidos: list[dict[str, Any]] = []

    async def accept(self) -> None:
        """Acepta el handshake (no hace nada)."""

    async def send_json(self, mensaje: dict[str, Any]) -> None:
        """Registra el mensaje recibido."""
        self.recibidos.append(mensaje)


async def _limpiar() -> None:
    async with SessionLocal() as session:
        for tabla in (
            "events",
            "ranking_por_sesion",
            "distribucion_por_pregunta",
            "pregunta_plantilla",
            "banco",
            "comision_docentes",
            "estudiante",
            "comision",
            "materia",
            "administrador",
            "usuario",
        ):
            await session.execute(text(f"DELETE FROM {tabla}"))
        await session.commit()


def _docente() -> dict[str, str]:
    return headers_de(uuid.uuid4(), TipoPerfil.DOCENTE)


def percentil(muestras: list[float], p: float) -> float:
    """Percentil por rango más cercano (nearest-rank) sobre `muestras`."""
    ordenadas = sorted(muestras)
    return ordenadas[max(0, math.ceil(p / 100 * len(ordenadas)) - 1)]


def resumir(muestras_ms: list[float]) -> dict[str, float]:
    """Resume las muestras: n, mediana, p95, máximo, mínimo y desvío estándar (ms)."""
    return {
        "n": len(muestras_ms),
        "mediana_ms": round(statistics.median(muestras_ms), 2),
        "p95_ms": round(percentil(muestras_ms, 95), 2),
        "maximo_ms": round(max(muestras_ms), 2),
        "minimo_ms": round(min(muestras_ms), 2),
        "desvio_ms": round(statistics.stdev(muestras_ms), 2),
    }


async def _cierre_use_case(sesion_id: str) -> float:
    """Ejecuta `CerrarPreguntaActual` con dependencias reales y devuelve los ms del use case."""
    async with SessionLocal() as session:
        use_case = CerrarPreguntaActualUseCase(
            SQLAlchemyEventStore(session),
            SQLAlchemyProyeccionesEnVivoQuery(session),
            PreguntaConsultaPortInProcess(session),
            WebSocketCanalTiempoReal(get_connection_manager()),
            EstudianteConsultaPortInProcess(session),
        )
        inicio = time.perf_counter()
        await use_case.execute(uuid.UUID(sesion_id))
        return (time.perf_counter() - inicio) * 1000


async def _cierre_http(client: AsyncClient, sesion_id: str) -> float:
    """Cierra por `POST /cerrar-pregunta` vía ASGI y devuelve los ms de la request completa."""
    inicio = time.perf_counter()
    respuesta = await client.post(
        f"/sesiones-en-vivo/{sesion_id}/cerrar-pregunta", headers=_docente()
    )
    ms = (time.perf_counter() - inicio) * 1000
    assert respuesta.status_code == 200, respuesta.text
    return ms


async def _medir_modo(modo: str, estudiantes: list[tuple[str, dict[str, str]]]) -> list[float]:
    """Corre `SESIONES` sesiones de `PREGUNTAS_POR_SESION` preguntas y mide cada cierre."""
    muestras: list[float] = []
    manager = get_connection_manager()
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        for numero in range(SESIONES):
            sesion_id, _ = await preparar_sesion(opcion_multiple=True)
            for _, headers in estudiantes:
                respuesta = await client.post(
                    f"/sesiones-en-vivo/{sesion_id}/unirse", headers=headers
                )
                assert respuesta.status_code == 200, respuesta.text
            await iniciar_sesion(sesion_id)
            conexiones = [ConexionSimulada() for _ in range(PARTICIPANTES)]
            for conexion in conexiones:
                await manager.conectar(uuid.UUID(sesion_id), conexion)  # type: ignore[arg-type]

            for indice in range(PREGUNTAS_POR_SESION):
                if indice > 0:
                    await client.post(f"/sesiones-en-vivo/{sesion_id}/avanzar", headers=_docente())
                await client.post(
                    f"/sesiones-en-vivo/{sesion_id}/mostrar-opciones", headers=_docente()
                )
                pregunta_id = await _pregunta_id(sesion_id, indice)
                respuestas = await asyncio.gather(
                    *[
                        client.post(
                            f"/sesiones-en-vivo/{sesion_id}/responder",
                            json={"pregunta_id": pregunta_id, "contenido": {"opcion_indice": 1}},
                            headers=headers,
                        )
                        for _, headers in estudiantes
                    ]
                )
                assert all(r.status_code == 200 for r in respuestas), "fallaron respuestas"
                muestras.append(
                    await _cierre_use_case(sesion_id)
                    if modo == "use_case"
                    else await _cierre_http(client, sesion_id)
                )
            cierres = [
                sum(1 for m in c.recibidos if m["tipo"] == "pregunta_cerrada") for c in conexiones
            ]
            assert cierres == [PREGUNTAS_POR_SESION] * PARTICIPANTES, "no llegó a todos"
            print(
                f"  [{modo}] sesión {numero + 1}/{SESIONES} ok — último cierre {muestras[-1]:.1f} ms"
            )
    return muestras


async def _pregunta_id(sesion_id: str, indice: int) -> str:
    async with SessionLocal() as session:
        eventos = await SQLAlchemyEventStore(session).load(
            "ActividadEvaluativaEnVivo", uuid.UUID(sesion_id)
        )
    return eventos[0].payload["preguntas"][indice]["pregunta_id"]


async def main() -> int:
    """Ejecuta la medición, imprime el resumen, guarda la evidencia y devuelve el exit code."""
    await _limpiar()
    try:
        _, comision_id = await preparar_sesion(opcion_multiple=True)
        estudiantes = await crear_estudiantes(comision_id, PARTICIPANTES)
        print(f"{PARTICIPANTES} Estudiantes creados. Midiendo (criterio: use case)...")
        use_case = resumir(await _medir_modo("use_case", estudiantes))
        print("Midiendo (complementaria: POST HTTP vía ASGI)...")
        http = resumir(await _medir_modo("http", estudiantes))
    finally:
        await _limpiar()

    veredicto = "CUMPLE" if use_case["p95_ms"] <= UMBRAL_MS else "NO CUMPLE"
    evidencia = {
        "us": "US-6.2.9 (re-medido por US-6.3.1, resolución de nombres sumada al camino)",
        "fecha": datetime.now(UTC).isoformat(),
        "entorno": {
            "maquina": platform.platform(),
            "python": platform.python_version(),
            "base_de_datos": "PostgreSQL local (NullPool)",
            "conexiones": f"{PARTICIPANTES} simuladas en el ConnectionManager real",
        },
        "criterio": {"medicion": "use case CerrarPreguntaActual", "p95_maximo_ms": UMBRAL_MS},
        "participantes": PARTICIPANTES,
        "use_case": use_case,
        "http_complementaria": http,
        "veredicto": veredicto,
    }
    EVIDENCIA.parent.mkdir(parents=True, exist_ok=True)
    EVIDENCIA.write_text(json.dumps(evidencia, indent=2, ensure_ascii=False) + "\n")
    print(json.dumps(evidencia, indent=2, ensure_ascii=False))
    print(
        f"\nVeredicto: {veredicto} (p95 use case = {use_case['p95_ms']} ms, umbral {UMBRAL_MS} ms)"
    )
    print(f"Evidencia guardada en {EVIDENCIA}")
    return 0 if veredicto == "CUMPLE" else 1


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
