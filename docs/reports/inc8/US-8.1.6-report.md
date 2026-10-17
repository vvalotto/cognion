# Reporte — US-8.1.6: Servir el frontend desde la misma imagen y el mismo origen

**Estado:** implementada en `feature/US-8.1.1-cors-configurable` (2026-10-16). PR diferido al cierre de la Iteración 1.
**Issue:** #519 · **Spec:** `docs/specs/inc8/US-8.1.6.md`

## Problema de diseño detectado
La API no tiene prefijo y comparte rutas con el frontend (`/materias`, `/comisiones`, `/actividades`…). Servir ambos en la raíz habría hecho que recargar o abrir un link a `/materias` devolviera JSON. Se montó la API bajo `/api`, el mismo contrato que ya usa el proxy de desarrollo de Vite.

## Qué se hizo
- `src/servidor.py`: `crear_servidor(directorio)` monta `src.app.app` (sin cambios) en `/api` y sirve `frontend/dist` en `/` con fallback a `index.html` para rutas del SPA. Una ruta con extensión inexistente es 404 (un build roto no se disfraza). Sin `dist` (desarrollo), solo monta la API.
- Propaga el `lifespan` de la API: Starlette no ejecuta el de una app montada, y sin esto el `VerificadorDeVencimientos` (`US-3.2.4`) habría dejado de correr sin ningún error visible. Cubierto por un test.
- `Dockerfile`: `CMD` arranca `src.servidor:servidor` con `--proxy-headers --forwarded-allow-ips "*"` (detrás de Fly las redirecciones deben conservar `https`); `ARG VITE_API_BASE_URL` pasa a `/api`.
- `fly.toml`: healthcheck a `/api/health`; test de `US-8.1.4` actualizado.
- `frontend/.env.example` aclara el valor del build.

## Verificación real
Build con `VITE_API_BASE_URL=/api` (queda embebido) y `uvicorn src.servidor:servidor` sobre una base descartable (migraciones + bootstrap de `US-8.1.4`/`8.1.5`): raíz y `/materias` sirven el SPA, asset 200 / inexistente 404, `/api/health` ok, `/api/materias` 401 sin token, login real devuelve token. Base borrada, sin errores en el log.

## Calidad
pylint 10.00, ruff/mypy 0 errores, `servidor.py` 100 % cobertura, suite unit 926/926. CodeGuard full: 4 errores de tooling.

## Límites
- No verificado con `docker build` ni en Fly.io (sin Docker local): lo cubren `US-8.2.1`/`US-8.4.3`.
- El WebSocket se probó en el servidor de pruebas (llega a la API bajo `/api`), no con una conexión real de punta a punta.
- Sin caché HTTP ni compresión (fuera de alcance). El `<title>` del `index.html` sigue siendo "frontend" (preexistente).
- Decisión propia, no pedida: se desactivan `/docs` y `/openapi.json` del servidor raíz; la documentación de la API queda en `/api/docs`.
