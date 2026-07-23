"""Punto de entrada de la API FastAPI de Cognion."""

from fastapi import FastAPI

from src.identidad.frameworks.api.comisiones_router import router as comisiones_router
from src.identidad.frameworks.api.invitaciones_router import router as invitaciones_router
from src.identidad.frameworks.api.usuarios_router import router as usuarios_router

app = FastAPI(title="Cognion", version="0.1.0")

app.include_router(usuarios_router)
app.include_router(comisiones_router)
app.include_router(invitaciones_router)


@app.get("/health", tags=["infra"])
async def health() -> dict[str, str]:
    """Reporta que el servicio está arriba."""
    return {"status": "ok"}
