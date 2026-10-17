"""Servidor de despliegue: la API bajo `/api` y el frontend compilado en la raíz (`US-8.1.6`).

La API no tiene prefijo y comparte rutas con el frontend (`/materias`, `/comisiones`...), por eso
se monta bajo `/api`, el mismo contrato que el proxy de desarrollo de Vite. `src.app.app` no cambia.
"""

from __future__ import annotations

from pathlib import Path

from fastapi import FastAPI
from starlette.exceptions import HTTPException
from starlette.responses import Response
from starlette.staticfiles import StaticFiles
from starlette.types import Scope

from src.app import app as api

DIRECTORIO_FRONTEND = Path(__file__).resolve().parent.parent / "frontend" / "dist"


class _ArchivosEstaticosSpa(StaticFiles):
    """Sirve los archivos del build y devuelve `index.html` para las rutas del SPA.

    Una ruta con extensión que no existe (`/assets/x.js`) sigue siendo 404: devolver `index.html`
    ahí ocultaría un build roto.
    """

    async def get_response(self, path: str, scope: Scope) -> Response:
        """Resuelve el archivo; si es una ruta del SPA sin archivo, responde `index.html`."""
        try:
            return await super().get_response(path, scope)
        except HTTPException as error:
            if error.status_code == 404 and "." not in Path(path).name:
                return await super().get_response("index.html", scope)
            raise


def crear_servidor(directorio_frontend: Path) -> FastAPI:
    """Arma el servidor: API en `/api` y, si existe `directorio_frontend`, el SPA en `/`."""
    # Starlette no ejecuta el `lifespan` de una app montada: se propaga el de la API para que siga
    # corriendo el `VerificadorDeVencimientos` (`US-3.2.4`).
    aplicacion = FastAPI(
        lifespan=api.router.lifespan_context, openapi_url=None, docs_url=None, redoc_url=None
    )
    aplicacion.mount("/api", api)
    if directorio_frontend.is_dir():
        aplicacion.mount("/", _ArchivosEstaticosSpa(directory=directorio_frontend, html=True))
    return aplicacion


servidor = crear_servidor(DIRECTORIO_FRONTEND)
