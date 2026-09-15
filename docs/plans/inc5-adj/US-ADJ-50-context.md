# Contexto de Ejecución — US-ADJ-50

## Fuentes
- **Fuente HU:** Documento local — `docs/specs/ajustes/US-ADJ-50.md`
- **Fuente Arquitectura:** `docs/rf/ARQ_v1.md` + `CLAUDE.md` (arquitectura ya decidida, no se pregunta)

## Historia de Usuario
- **ID:** US-ADJ-50
- **Título:** Docente ve el ranking de "Preguntas más falladas"
- **Tipo:** Nueva funcionalidad (frontend puro)
- **Puntos:** 3
- **Prioridad:** Alta — completa RF-22 (par backend→frontend), backend ya cerrado en `US-ADJ-46`

## Decisiones de Ejecución
- **BDD:** No — mismo criterio que `US-ADJ-48`/`US-ADJ-49`/`US-4.2.5`/`US-4.2.6`: US de frontend
  puro sobre backend ya validado por BDD propio (`US-ADJ-46`); cobertura de comportamiento vía
  Vitest, no Gherkin/pytest-bdd (que aplica a `tests/features/incN` del backend).
- **skip_bdd:** true
- **Fases a ejecutar:** 0, 2, 3, 4 (Vitest en lugar de pytest), 7 (oxlint + tsc + coverage frontend), 8, 9
  (Fases 1, 5, 6 no aplican — sin backend nuevo, sin BDD)

## Perfil Activo
- **Perfil:** clean-architecture-bc
- **Patrón arquitectónico:** clean-architecture (no aplica a este componente — frontend React/TS puro, sin capas del backend)
- **Umbrales de calidad (frontend, según convención ya usada en Iteración 4):**
  - oxlint: 0 errores
  - `tsc -b` (build real, no `--noEmit` sin `-b`): 0 errores
  - Vitest: 100% de los tests nuevos en verde, sin romper la suite existente
  - Cobertura de branches del frontend ≥ 80% global (umbral de `US-ADJ-16`)

## Rutas de Artefactos
- Contexto: `docs/plans/inc5-adj/US-ADJ-50-context.md`
- BDD feature: N/A (skip_bdd)
- Plan: `docs/plans/inc5-adj/US-ADJ-50-plan.md`
- Reporte: `docs/reports/inc5-adj/US-ADJ-50-report.md`
- Quality report: `quality/reports/inc5-adj/US-ADJ-50-quality.json`
