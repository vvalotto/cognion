# Plan de Implementación — US-8.1.1

| # | Tarea | Archivo |
|---|-------|---------|
| 1 | `Settings.cors_allowed_origins: str = "http://localhost:5173"` y propiedad `cors_origins_list` (split por coma, trim, sin vacíos) | `src/settings.py` |
| 2 | Validación: si la lista contiene `*` → `ValueError` claro al construir `Settings` (validator pydantic) | `src/settings.py` |
| 3 | `CORSMiddleware(allow_origins=settings.cors_origins_list)` | `src/app.py` |
| 4 | Tests unitarios: parseo (default, múltiples con espacios, vacíos), rechazo de `*` | `tests/unit/inc8/test_us_8_1_1_cors_settings.py` |
| 5 | Test de integración: preflight `OPTIONS` con origen permitido / no permitido sobre `app` (sin tocar la base) | `tests/integration/inc8/test_us_8_1_1_cors.py` |
| 6 | Documentar `CORS_ALLOWED_ORIGINS` en `.env.example` si existe | `.env.example` |

Sin cambios de dominio, BC ni frontend. Estimación: baja complejidad.
