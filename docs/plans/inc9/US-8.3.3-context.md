# Contexto de Ejecución — US-8.3.3

## Fuentes
- **Fuente HU:** `docs/specs/inc8/US-8.3.3.md`, Issue [#526](https://github.com/vvalotto/cognion/issues/526)
- **Fuente UX:** no aplica (sin cambios en `frontend/`)
- **Origen:** plan del Incremento 8 (`docs/plans/inc8/inc8-candidatas.md`); decisiones de Víctor del 2026-11-08 (readiness como endpoint nuevo, `LOG_FORMAT=texto|json` con `texto` por defecto)
- **Código existente:** `src/app.py` (`/health`, `configurar_logging(settings.log_level)`), `src/shared/frameworks/logging_config.py` (`configurar_logging`, `FiltroTokens`, `_HandlerCognion`, `enmascarar_tokens`), `src/settings.py` (`log_level`), `src/shared/frameworks/db.py` (`SessionLocal`), `deploy/gcp/cognion.sh` (`estado`), `deploy/gcp/docker-compose.yml` (healthcheck sobre `/api/health`). Pruebas con proceso real: `tests/integration/inc8/_servidor_real.py` (`ServidorReal`)

## Historia de Usuario
- **ID:** US-8.3.3 — Observabilidad mínima: logs estructurados y healthcheck de readiness
- **Tipo:** mejora de operación, backend (infraestructura compartida + aplicación)
- **Puntos:** 5 · **Patrón activo:** `clean-architecture-bc`
- **Iteración:** Incremento 9, Iteración 3 (rama `feature/inc-9-iter-3-guardas-y-observabilidad`, un commit por ítem y un solo PR al cierre)

## Decisiones de Ejecución
- **Readiness en `src/app.py`**, junto a `/health`, sin pasar por ningún BC: usa `SessionLocal` de `shared/frameworks/db.py` y `asyncio.wait_for` (2 s). El `503` no incluye el motivo; el error real va al log sin credenciales.
- **`FormateadorJson`** en `logging_config.py`: `ts` (UTC, ISO 8601), `nivel`, `logger`, `mensaje` y `excepcion` si hay. Vuelve a enmascarar el mensaje ya formateado y el traceback, porque el filtro solo sanea `msg` y `args`.
- **`configurar_logging(nivel, formato)`** sigue siendo idempotente; en modo `json` cambia el formatter de los handlers de `uvicorn` ya existentes en lugar de crear otros. `settings.log_format: Literal["texto", "json"] = "texto"` valida el valor al arrancar.
- **`cognion.sh estado`** muestra `/api/health` y `/api/health/ready`; la parte que arma el resumen se puede probar con un `curl` simulado.
- **Sin cambios** en `docker-compose.yml`, `desplegar.sh`, el frontend, los BC ni los puertos.
- **Tests:** unitarios del formateador y del filtro (sin base); integración con `ServidorReal` (`uvicorn` real, base descartable inline) para los logs de acceso y las variables de entorno; BDD de punta a punta; el `503` se prueba con una sesión que falla, nunca tocando la base de desarrollo.
- **Fases:** todas, con BDD.

## Rutas
- Plan: docs/plans/inc9/US-8.3.3-plan.md · Reporte: docs/reports/inc9/US-8.3.3-report.md · Quality: quality/reports/inc9/US-8.3.3-quality.json
- Feature: tests/features/inc9/US-8.3.3-observabilidad.feature
