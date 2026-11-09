# Contexto de Ejecución — US-9.4.2

## Fuentes
- **Fuente HU:** `docs/specs/inc9/US-9.4.2.md`, Issue [#601](https://github.com/vvalotto/cognion/issues/601)
- **Fuente arquitectura:** `docs/adr/ADR-026-acoplamiento-entre-bc-por-datos.md`, `CLAUDE.md`
- **Código existente:** `src/actividad_evaluativa/frameworks/adapters/estudiante_consulta_port_in_process.py`, `src/identidad/entities/ports/cuenta_query_port.py`, `src/identidad/interface_adapters/gateways/cuenta_query_repository.py`

## Historia de Usuario
- **ID:** US-9.4.2 — Actividad Evaluativa deja de leer `UsuarioModel` de Identidad
- **Tipo:** refactorización sin cambio de comportamiento (backend) · **Puntos:** 2 · **Patrón activo:** `clean-architecture-bc`
- **Iteración:** Incremento 9, Iteración 4 (misma rama que `US-9.4.1`; un commit por US, PR único al cierre)

## Decisiones de Ejecución
- **BDD:** No (refactorización); se saltean Fases 1 y 6. Los escenarios se cubren con un test de caracterización de integración (primer commit, antes de migrar) y `lint-imports`.
- **Fases a ejecutar:** 0, 2, 3, 4, 5, 7, 8, 9.
- **Base de datos:** integración con `DATABASE_URL` inline a una base descartable. El `postgresql@16` de Homebrew no arranca (`postmaster.pid` viejo): se usa un cluster propio en el scratchpad, puerto 55432, con `LC_ALL=en_US.UTF-8` y socket en `/tmp/pgcog`.

## Rutas
- Plan: docs/plans/inc9/US-9.4.2-plan.md · Reporte: docs/reports/inc9/US-9.4.2-report.md · Quality: quality/reports/inc9/US-9.4.2-quality.json
