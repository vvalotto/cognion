# Plan de Implementación — US-8.1.6

| # | Tarea | Archivo |
|---|-------|---------|
| 1 | `crear_servidor(directorio)`: monta la API en `/api`, sirve el SPA con fallback a `index.html`, propaga el `lifespan` | `src/servidor.py` |
| 2 | `CMD` con `src.servidor:servidor` + `--proxy-headers`; `ARG VITE_API_BASE_URL=/api` | `Dockerfile` |
| 3 | Healthcheck a `/api/health` | `fly.toml` |
| 4 | Tests unitarios (6 escenarios, con un `dist` temporal) + test del CMD/ARG/healthcheck | `tests/unit/inc8/test_us_8_1_6_servidor.py` |
| 5 | Actualizar test de `fly.toml` de US-8.1.4 (healthcheck) | `tests/unit/inc8/test_us_8_1_4_migraciones_release.py` |
| 6 | Verificación real: build del frontend + uvicorn local sirviendo ambos desde un origen | evidencia en el reporte |

`src/app.py` no se modifica. Sin cambios de frontend (la base `/api` entra por el build, `US-8.1.2`).
