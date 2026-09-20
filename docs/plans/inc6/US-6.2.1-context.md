# Contexto de Ejecución — US-6.2.1

## Fuentes
- **Fuente HU:** `docs/specs/inc6/US-6.2.1.md`, GitHub Issue [#392](https://github.com/vvalotto/cognion/issues/392)
- **Fuente Arquitectura:** `CLAUDE.md` (§Arquitectura interna) + `docs/design/domain/BC-actividad-evaluativa-modelo.md` §14, §17 + `docs/plans/inc6/inc6-candidatas.md` §Spike RF-10

## Historia de Usuario
- **ID:** US-6.2.1
- **Título:** Cálculo de puntaje server-side de una respuesta en vivo
- **Tipo:** Técnica (servicio de dominio puro + operación nueva en puerto existente), sin endpoint
- **Puntos:** 3
- **Prioridad:** Alta — base de `US-6.2.4`

## Decisiones de Ejecución
- **BDD:** No — mismo precedente que `US-3.1.1`/`US-6.1.1` (`skip_bdd: true`, indicado por la propia spec): los 6 escenarios quedan cubiertos uno a uno por tests unitarios/integración.
- **skip_bdd:** true
- **Fases a ejecutar:** 0, 2, 3, 4, 5, 7, 8, 9 (se saltean 1 y 6)

## Perfil Activo
- **Perfil:** clean-architecture-bc
- **Patrón:** clean-architecture (entities → use_cases → interface_adapters → frameworks, BC-first)
- **Umbrales:** pylint ≥ 8.0, CC ≤ 10, MI ≥ 20, cobertura ≥ 95.0%

## Rutas de Artefactos
- Contexto: docs/plans/inc6/US-6.2.1-context.md
- Plan: docs/plans/inc6/US-6.2.1-plan.md
- Reporte: docs/reports/inc6/US-6.2.1-report.md
- Quality report: quality/reports/inc6/US-6.2.1-quality.json

## Notas específicas del proyecto
- Rutas en subcarpeta `incN/`. CodeGuard con `--analysis-type full`. `designreviewer` con `--config pyproject.toml`.
- `tests/unit/` no toca la DB; `tests/integration/` sí y la vacía (DB local compartida) — sin prueba manual en curso, sin overlap.
