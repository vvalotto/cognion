# Contexto de Ejecución — US-8.5.1

## Fuentes
- **Fuente HU:** `docs/specs/inc8/US-8.5.1.md`, Issue [#536](https://github.com/vvalotto/cognion/issues/536)
- **Fuente Arquitectura:** `CLAUDE.md`, `ADR-021`, `ADR-024`

## Historia de Usuario
- **ID:** US-8.5.1 — Entorno local: `ENTORNO=local` con secreto fuerte para uso en red
- **Tipo:** infra backend técnica (transversal, `src/settings.py`), sin comando de negocio
- **Puntos:** 3

## Decisiones de Ejecución
- **skip_bdd:** true — mismo precedente que `US-8.1.3`: los 5 escenarios de la spec se cubren con tests unitarios.
- **Fases a ejecutar:** 0, 2, 3, 4, 7, 8, 9 (sin integración: no hay DB ni HTTP involucrados)

## Perfil Activo
- clean-architecture-bc; umbrales: pylint ≥ 8.0, CC ≤ 10, MI ≥ 20, cobertura ≥ 95%

## Rutas
- Plan: docs/plans/inc8/US-8.5.1-plan.md
- Reporte: docs/reports/inc8/US-8.5.1-report.md
- Quality: quality/reports/inc8/US-8.5.1-quality.json

## Notas
- No correr pytest contra la base de desarrollo: `tests/unit/` es seguro (no toca la DB).
