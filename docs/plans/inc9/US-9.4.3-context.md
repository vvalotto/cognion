# Contexto de Ejecución — US-9.4.3

## Fuentes
- **Fuente HU:** `docs/specs/inc9/US-9.4.3.md`, Issue [#602](https://github.com/vvalotto/cognion/issues/602)
- **Fuente arquitectura:** `docs/adr/ADR-026-acoplamiento-entre-bc-por-datos.md`, `CLAUDE.md`
- **Código existente:** `src/identidad/frameworks/adapters/evaluacion_consulta_port_in_process.py`, `src/actividad_evaluativa/frameworks/adapters/evaluacion_estudiante_query_repository.py` (patrón a seguir), `src/actividad_evaluativa/frameworks/event_store/sqlalchemy_event_store.py`

## Historia de Usuario
- **ID:** US-9.4.3 — Identidad deja de leer `EventoModel` de Actividad Evaluativa
- **Tipo:** refactorización sin cambio de comportamiento (backend) · **Puntos:** 3 · **Patrón activo:** `clean-architecture-bc`
- **Iteración:** Incremento 9, Iteración 4 (misma rama que `US-9.4.1` y `US-9.4.2`; un commit por US, PR único al cierre)

## Decisiones de Ejecución
- **BDD:** No (refactorización); se saltean Fases 1 y 6. Los escenarios se cubren con un test de caracterización de integración (primer commit) y `lint-imports`.
- **Fases a ejecutar:** 0, 2, 3, 4, 5, 7, 8, 9.
- **Base de datos:** integración con `DATABASE_URL` inline a una base descartable. El `postgresql@16` de Homebrew sigue sin arrancar (`postmaster.pid` viejo): cluster propio en el scratchpad, puerto 55432, `LC_ALL=en_US.UTF-8`, socket en `/tmp/pgcog`.
- **CBO:** correr `designreviewer` en la Fase 7 (lección de `US-9.4.2`).

## Rutas
- Plan: docs/plans/inc9/US-9.4.3-plan.md · Reporte: docs/reports/inc9/US-9.4.3-report.md · Quality: quality/reports/inc9/US-9.4.3-quality.json
