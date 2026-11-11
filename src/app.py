"""Punto de entrada de la API FastAPI de Cognion."""

import asyncio
import contextlib
import logging
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import Depends, FastAPI, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from src.actividad_evaluativa.frameworks.api.actividades_router import router as actividades_router
from src.actividad_evaluativa.frameworks.api.evaluaciones_router import (
    router as evaluaciones_router,
)
from src.actividad_evaluativa.frameworks.api.revision_router import router as revision_router
from src.actividad_evaluativa.frameworks.api.sesiones_en_vivo_router import (
    router as sesiones_en_vivo_router,
)
from src.actividad_evaluativa.frameworks.dependencies import (
    build_verificar_vencimientos_use_case,
)
from src.analytics.frameworks.api.analytics_router import router as analytics_router
from src.banco_preguntas.frameworks.api.bancos_router import router as bancos_router
from src.banco_preguntas.frameworks.api.materias_router import router as materias_router
from src.banco_preguntas.frameworks.api.preguntas_router import router as preguntas_router
from src.identidad.frameworks.api.auth_router import router as auth_router
from src.identidad.frameworks.api.autoregistro_router import router as autoregistro_router
from src.identidad.frameworks.api.comisiones_router import router as comisiones_router
from src.identidad.frameworks.api.cuentas_router import router as cuentas_router
from src.identidad.frameworks.api.estudiante_router import router as estudiante_router
from src.identidad.frameworks.api.invitaciones_grupales_router import (
    router as invitaciones_grupales_router,
)
from src.identidad.frameworks.api.invitaciones_router import router as invitaciones_router
from src.identidad.frameworks.api.materias_comisiones_router import (
    router as identidad_materias_comisiones_router,
)
from src.identidad.frameworks.api.perfil_router import router as perfil_router
from src.identidad.frameworks.api.recuperacion_password_router import (
    router as recuperacion_password_router,
)
from src.identidad.frameworks.api.registro_router import router as registro_router
from src.identidad.frameworks.api.usuarios_router import router as usuarios_router
from src.settings import settings
from src.shared.frameworks.db import SessionLocal
from src.shared.frameworks.logging_config import configurar_logging
from src.shared.frameworks.salud import comprobar_base
from src.shared.frameworks.version import obtener_version

configurar_logging(settings.log_level, settings.log_format)

logger = logging.getLogger(__name__)


async def _verificar_vencimientos_periodicamente() -> None:
    """Corre `VerificarVencimientosUseCase` cada `verificador_vencimientos_cadencia_segundos`.

    Background task del `VerificadorDeVencimientos` (`US-3.2.4`) — abre su propia sesión por
    corrida, ya que no hay un ciclo request/response de FastAPI del que colgarse. Una corrida
    fallida (ej. error transitorio de conexión a la BD) se loguea y no mata el loop.
    """
    while True:
        await asyncio.sleep(settings.verificador_vencimientos_cadencia_segundos)
        try:
            async with SessionLocal() as session:
                await build_verificar_vencimientos_use_case(session).execute()
        except Exception:
            logger.exception("VerificarVencimientosUseCase falló en una corrida periódica")


@asynccontextmanager
async def lifespan(_: FastAPI) -> AsyncIterator[None]:
    """Arranca y detiene el background task del `VerificadorDeVencimientos` (`US-3.2.4`)."""
    tarea = asyncio.create_task(_verificar_vencimientos_periodicamente())
    yield
    tarea.cancel()
    with contextlib.suppress(asyncio.CancelledError):
        await tarea


app = FastAPI(title="Cognion", version=obtener_version(), lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(usuarios_router)
app.include_router(cuentas_router)
app.include_router(perfil_router)
app.include_router(comisiones_router)
app.include_router(identidad_materias_comisiones_router)
app.include_router(estudiante_router)
app.include_router(invitaciones_router)
app.include_router(invitaciones_grupales_router)
app.include_router(registro_router)
app.include_router(autoregistro_router)
app.include_router(recuperacion_password_router)
app.include_router(auth_router)
app.include_router(materias_router)
app.include_router(preguntas_router)
app.include_router(bancos_router)
app.include_router(actividades_router)
app.include_router(evaluaciones_router)
app.include_router(revision_router)
app.include_router(sesiones_en_vivo_router)
app.include_router(analytics_router)


@app.get("/health", tags=["infra"])
async def health() -> dict[str, str]:
    """Reporta que el servicio está arriba y qué versión corre (`US-10.2.1`)."""
    return {"status": "ok", "version": obtener_version()}


@app.get("/health/ready", tags=["infra"])
async def health_ready(base_disponible: bool = Depends(comprobar_base)) -> JSONResponse:
    """Reporta si la aplicación puede atender pedidos: comprueba que la base de datos responde.

    A diferencia de `/health` (el proceso está vivo), responde 503 si la base no está disponible.
    El cuerpo no incluye el motivo; el error real queda en el log, sin credenciales (`US-8.3.3`).
    """
    if base_disponible:
        return JSONResponse({"status": "ok", "base_de_datos": "ok"})
    return JSONResponse(
        {"status": "error", "base_de_datos": "no disponible"},
        status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
    )
