# Contexto de Ejecución — US-6.2.3

## Fuentes
- **Fuente HU:** `docs/specs/inc6/US-6.2.3.md`, GitHub Issue [#394](https://github.com/vvalotto/cognion/issues/394)
- **Fuente Arquitectura:** `CLAUDE.md` (§Arquitectura interna) + `docs/design/domain/BC-actividad-evaluativa-modelo.md` §15, §16 + `ADR-009`

## Historia de Usuario
- **ID:** US-6.2.3
- **Título:** Read models de ranking e histograma de la sesión en vivo
- **Tipo:** Técnica (infra backend, tablas + migración + puertos + adapter), sin endpoint
- **Puntos:** 3
- **Prioridad:** Alta — base de `US-6.2.4`, `6.2.5`, `6.2.7`, `6.2.8`

## Decisiones de Ejecución
- **BDD:** No — la spec indica `skip_bdd: true` (técnica); los escenarios quedan cubiertos por tests de integración.
- **skip_bdd:** true
- **Fases a ejecutar:** 0, 2, 3, 4, 5, 7, 8, 9

## Perfil Activo
- **Perfil:** clean-architecture-bc
- **Umbrales:** pylint ≥ 8.0, CC ≤ 10, MI ≥ 20, cobertura ≥ 95.0%

## Rutas de Artefactos
- Contexto: docs/plans/inc6/US-6.2.3-context.md
- Plan: docs/plans/inc6/US-6.2.3-plan.md
- Reporte: docs/reports/inc6/US-6.2.3-report.md
- Quality report: quality/reports/inc6/US-6.2.3-quality.json

## Notas específicas del proyecto
- Rutas en subcarpeta `incN/`. CodeGuard con `--analysis-type full` y `.venv/bin` en el `PATH`. `designreviewer` con `--config pyproject.toml`.
- Migración con backfill/round-trip verificado contra la DB real (upgrade → downgrade → upgrade), como `US-2.1.2`.
- El 5° puerto de `UnirseASesionEnVivoUseCase` puede disparar CBO en el pre-push (lección de `US-2.1.2`/`2.1.5`): verificar antes de dar por cerrada la Fase 7.
