from fastapi import FastAPI

from src.identidad.frameworks.api.comisiones_router import router as comisiones_router
from src.identidad.frameworks.api.usuarios_router import router as usuarios_router

app = FastAPI(title="Cognion", version="0.1.0")

app.include_router(usuarios_router)
app.include_router(comisiones_router)


@app.get("/health", tags=["infra"])
async def health() -> dict[str, str]:
    return {"status": "ok"}
