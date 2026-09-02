# Contexto de Ejecución — US-ADJ-20

## Fuentes
- **Fuente HU:** Documento local — `docs/specs/ajustes/US-ADJ-20.md`
- **Fuente Arquitectura:** `docs/rf/ARQ_v1.md` + `CLAUDE.md` (Clean Architecture interna,
  perfil `clean-architecture-bc`)

## Historia de Usuario
- **ID:** US-ADJ-20
- **Título:** `AbortController` en los fetch de `useEffect`/submit del frontend
- **Tipo:** Refactorización — corrección de robustez técnica (sin cambio de comportamiento
  observable para el usuario)
- **Puntos:** 5
- **Prioridad:** Alta (causa raíz de un flake intermitente en CI, confirmado en dos PRs de
  Dependabot no relacionados)

## Decisiones de Ejecución
- **BDD:** No — es una refactorización sin cambio de comportamiento observable (tabla de
  clasificación de Fase 0: "Refactorización (sin cambio de comportamiento)" → BDD no aplica).
  La spec ya incluye escenarios Gherkin como criterios de verificación técnica (no como BDD
  ejecutable de dominio), suficientes para guiar la Fase 4/5.
- **skip_bdd:** true
- **Fases a ejecutar:** 0, 2, 3, 4, 5, 7, 8, 9 (se saltan 1 y 6)

## Perfil Activo
- **Perfil:** `clean-architecture-bc`
- **Patrón arquitectónico:** Clean Architecture interna por BC (no aplica en este caso — el
  cambio es transversal en `frontend/`, no toca `entities/use_cases/interface_adapters/frameworks`
  del backend)
- **Umbrales de calidad (frontend):**
  - oxlint: 0 errores
  - `tsc --noEmit`: 0 errores
  - `npx vitest run`: en verde, sin `unhandled rejection`

## Rutas de Artefactos
- Contexto: `docs/plans/US-ADJ-20-context.md`
- BDD feature: N/A (skip_bdd)
- Plan: `docs/plans/US-ADJ-20-plan.md`
- Reporte: `docs/reports/US-ADJ-20-report.md`
- Quality report: `quality/reports/US-ADJ-20-quality.json`
