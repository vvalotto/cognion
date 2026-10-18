# Contexto de Ejecución — US-8.5.2

## Fuentes
- **Fuente HU:** `docs/specs/inc8/US-8.5.2.md`, Issue [#537](https://github.com/vvalotto/cognion/issues/537)
- **Fuente Arquitectura:** `CLAUDE.md`, `ADR-023`

## Historia de Usuario
- **ID:** US-8.5.2 — Canal de email por consola para uso sin SMTP
- **Tipo:** infra backend técnica (transversal: `src/shared/frameworks/smtp.py`, `src/settings.py`)
- **Puntos:** 3

## Decisiones de Ejecución
- **skip_bdd:** true — mismo precedente que `US-8.1.x`/`US-8.5.1`; los 4 escenarios se cubren con tests unitarios.
  El escenario 4 (recuperación de contraseña) se cubre con un test unitario del caso de uso con el canal real en modo consola.
- **Fases a ejecutar:** 0, 2, 3, 4, 7, 8, 9
- **Branch:** `feature/US-8.5.1-entorno-local` (se apilan las US de la Iteración 5; PR único al cierre, decisión de Víctor)

## Perfil Activo
- clean-architecture-bc; umbrales: pylint ≥ 8.0, CC ≤ 10, MI ≥ 20, cobertura ≥ 95%

## Rutas
- Plan: docs/plans/inc8/US-8.5.2-plan.md
- Reporte: docs/reports/inc8/US-8.5.2-report.md
- Quality: quality/reports/inc8/US-8.5.2-quality.json

## Notas
- No correr integración/BDD contra la base de desarrollo; `tests/unit/` es seguro.
