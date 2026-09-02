# Contexto de Ejecución — US-3.2.2

## Fuentes
- **Fuente HU:** GitHub Issue [#156](https://github.com/vvalotto/cognion/issues/156) + spec `docs/specs/inc3/US-3.2.2.md`
- **Fuente Arquitectura:** `docs/rf/ARQ_v1.md` + `CLAUDE.md` (Clean Architecture BC-first) + código existente del BC (`US-3.1.1` a `US-3.2.1`)

## Historia de Usuario
- **ID:** US-3.2.2
- **Título:** Estudiante suspende y reanuda su evaluación
- **Tipo:** Nueva funcionalidad
- **Puntos:** 3
- **Prioridad:** Alta — bloquea `US-3.2.3` (finalizar desde `Suspendida`) y `US-3.2.4` (`VerificadorDeVencimientos` Regla 1)

## Decisiones de Ejecución
- **BDD:** Sí — nueva funcionalidad con criterios de aceptación claros (Gherkin ya redactado en la spec)
- **skip_bdd:** false
- **Fases a ejecutar:** 0, 1, 2, 3, 4, 5, 6, 7, 8, 9

## Perfil Activo
- **Perfil:** clean-architecture-bc
- **Patrón arquitectónico:** clean-architecture (entities → use_cases → interface_adapters → frameworks, BC-first)
- **Umbrales de calidad:**
  - pylint ≥ 8.0 (perfil base; histórico del BC ronda 9.2+)
  - CC ≤ 10
  - MI ≥ 20 (perfil base; histórico del BC ronda 40+)
  - cobertura ≥ 95%

## Rutas de Artefactos
- Contexto: docs/plans/inc3/US-3.2.2-context.md
- BDD feature: tests/features/inc3/US-3.2.2-suspender-reanudar-evaluacion.feature
- Plan: docs/plans/inc3/US-3.2.2-plan.md
- Reporte: docs/reports/inc3/US-3.2.2-report.md
- Quality report: quality/reports/inc3/US-3.2.2-quality.json
