"""Punto de entrada de la API FastAPI de Cognion."""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.actividad_evaluativa.frameworks.api.actividades_router import router as actividades_router
from src.banco_preguntas.frameworks.api.bancos_router import router as bancos_router
from src.banco_preguntas.frameworks.api.materias_router import router as materias_router
from src.banco_preguntas.frameworks.api.preguntas_router import router as preguntas_router
from src.identidad.frameworks.api.auth_router import router as auth_router
from src.identidad.frameworks.api.comisiones_router import router as comisiones_router
from src.identidad.frameworks.api.cuentas_router import router as cuentas_router
from src.identidad.frameworks.api.invitaciones_router import router as invitaciones_router
from src.identidad.frameworks.api.perfil_router import router as perfil_router
from src.identidad.frameworks.api.registro_router import router as registro_router
from src.identidad.frameworks.api.usuarios_router import router as usuarios_router

app = FastAPI(title="Cognion", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(usuarios_router)
app.include_router(cuentas_router)
app.include_router(perfil_router)
app.include_router(comisiones_router)
app.include_router(invitaciones_router)
app.include_router(registro_router)
app.include_router(auth_router)
app.include_router(materias_router)
app.include_router(preguntas_router)
app.include_router(bancos_router)
app.include_router(actividades_router)


@app.get("/health", tags=["infra"])
async def health() -> dict[str, str]:
    """Reporta que el servicio está arriba."""
    return {"status": "ok"}
