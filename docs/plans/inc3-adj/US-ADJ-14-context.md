# Contexto de Ejecución — US-ADJ-14

## Fuentes
- **Fuente HU:** Documento local — `docs/specs/ajustes/US-ADJ-14.md`
- **Fuente Arquitectura:** `docs/rf/ARQ_v1.md` + `CLAUDE.md` (Clean Architecture interna,
  perfil `clean-architecture-bc`) — no aplica al frontend en sí; el criterio de organización
  por BC ya existe en `frontend/src/lib/` y se extiende a `frontend/src/pages/`

## Historia de Usuario
- **ID:** US-ADJ-14
- **Título:** Reordenar `frontend/src/pages/` por Bounded Context
- **Tipo:** Refactorización (movimiento de archivos + imports, sin cambio de comportamiento)
- **Puntos:** 3
- **Prioridad:** Media (deuda de organización, sin impacto funcional)

## Decisiones de Ejecución
- **BDD:** No — refactorización sin cambio de comportamiento observable (tabla de
  clasificación de Fase 0). Los escenarios Gherkin de la spec son criterios de verificación
  técnica (suite en verde, mismas URLs), no BDD ejecutable de dominio.
- **skip_bdd:** true
- **Fases a ejecutar:** 0, 2, 3, 7, 8, 9 (se saltan 1, 4, 5 y 6 — sin tests nuevos, sin
  comportamiento nuevo a integrar; Fase 7 sí aplica porque hay código frontend movido y
  reescrito, a diferencia de `US-ADJ-13`)

## Perfil Activo
- **Perfil:** `clean-architecture-bc`
- **Patrón arquitectónico:** N/A para este cambio — transversal en `frontend/`, no toca
  `entities/use_cases/interface_adapters/frameworks` del backend
- **Umbrales de calidad (frontend):**
  - oxlint: 0 errores
  - `tsc --noEmit` (o `tsc -b`): 0 errores
  - `npx vitest run`: mismo número de tests que antes del refactor, en verde

## Rutas de Artefactos
- Contexto: `docs/plans/inc3-adj/US-ADJ-14-context.md`
- BDD feature: N/A (skip_bdd)
- Plan: `docs/plans/inc3-adj/US-ADJ-14-plan.md`
- Reporte: `docs/reports/inc3-adj/US-ADJ-14-report.md`
- Quality report: `quality/reports/inc3-adj/US-ADJ-14-quality.json`
