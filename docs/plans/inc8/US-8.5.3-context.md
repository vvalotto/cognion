# Contexto de Ejecución — US-8.5.3

## Fuentes
- **Fuente HU:** `docs/specs/inc8/US-8.5.3.md`, Issue [#538](https://github.com/vvalotto/cognion/issues/538)
- **Fuente Arquitectura:** `CLAUDE.md`, `ADR-016`, `US-8.1.5`/`US-8.1.6`

## Historia de Usuario
- **ID:** US-8.5.3 — Comando único para levantar y detener el despliegue local
- **Tipo:** tooling operativo (scripts en `scripts/local/`), sin código de producción
- **Puntos:** 3

## Decisiones de Ejecución
- **skip_bdd:** true — tooling de shell, sin `.feature`. Los 5 escenarios se verifican con un script de
  verificación propio (`tests/uat/inc8/verificar_levantar_local.sh`), mismo precedente que `verificar_migraciones.sh`.
- **Fases a ejecutar:** 0, 2, 3, 4 (verificación del script), 7 (shellcheck si está, ruff sobre lo Python), 8, 9. Sin 5/6.
- **Branch:** `feature/US-8.5.1-entorno-local` (apilada; PR único al cierre de la Iteración 5)

## Rutas
- Plan: docs/plans/inc8/US-8.5.3-plan.md · Reporte: docs/reports/inc8/US-8.5.3-report.md
- Quality: quality/reports/inc8/US-8.5.3-quality.json

## Notas
- Nunca tocar la base de desarrollo `cognion`; todo ocurre en `cognion_local` (verificación: base descartable propia).
- No hay Docker local; no se usa.
