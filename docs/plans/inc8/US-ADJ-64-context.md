# Contexto de Ejecución — US-ADJ-64

## Fuentes
- **Fuente HU:** `docs/specs/ajustes/US-ADJ-64.md`, Issue [#570](https://github.com/vvalotto/cognion/issues/570)
- **Origen:** UAT `US-8.7.2`, hallazgos #2 y #9 (`quality/reports/uat/inc8/registro-hallazgos.md`)
- **Arquitectura:** `CLAUDE.md` (Clean Architecture por BC; `shared/` admite las 4 capas para lo genuinamente transversal, `ADR-017`/`ADR-019`)

## Historia de Usuario
- **ID:** US-ADJ-64 — Logging local: los emails de consola se ven y los tokens no quedan completos en el log
- **Tipo:** fix de infraestructura transversal (`src/shared/frameworks/`); sin cambios en dominio, casos de uso ni frontend
- **Puntos:** 3 · **Patrón activo:** `clean-architecture-bc`

## Decisiones de Ejecución
- **Módulo nuevo** `src/shared/frameworks/logging_config.py`: `configurar_logging(nivel)` (idempotente) y un filtro que reemplaza el valor de `token=` por `token=***` en los loggers `uvicorn.access` y `uvicorn.error` (mensaje y argumentos). Se invoca una vez al importar `src/app.py`, que cubre `src.app:app` y `src.servidor:servidor`.
- **Handler solo en el logger `src`**, con `propagate` en verdadero: los tests existentes que usan `caplog` (`US-8.5.2`) siguen capturando; en un `uvicorn` real el logger raíz no tiene handlers, así que no hay líneas duplicadas.
- **`LOG_LEVEL`** como campo de `Settings` (`DEBUG|INFO|WARNING|ERROR`, por defecto `INFO`): un valor inválido falla al arrancar con la validación de Pydantic, que ya lista los valores válidos.
- **El cuerpo del email de consola conserva el link completo** (es el objetivo del modo consola): solo se enmascaran las URL de acceso.
- **Prueba con servidor real:** el escenario 1 de la spec no puede usar `caplog`; se arranca `python -m uvicorn src.app:app` como subproceso contra una base **descartable** y se lee su salida real. Se usa `src.app:app` y no `src.servidor:servidor` para no depender de `frontend/dist` en CI; la configuración vive en el import de `src.app`, común a ambos.
- **Fases:** todas, con BDD. Las pruebas de integración y BDD corren solo contra base descartable (`DATABASE_URL` inline), nunca `cognion_local` ni `cognion_uat`.

## Rutas
- Plan: docs/plans/inc8/US-ADJ-64-plan.md · Reporte: docs/reports/inc8/US-ADJ-64-report.md · Quality: quality/reports/inc8/US-ADJ-64-quality.json
- Feature: tests/features/inc8/US-ADJ-64-logging-local.feature
- Branch: `feature/US-ADJ-64-logging-local`, apilada sobre `fix/fechas-zona-horaria`; PR único al final de la Iteración 8.
