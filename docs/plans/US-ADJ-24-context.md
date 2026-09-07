# Contexto de Ejecución — US-ADJ-24

## Fuentes
- **Fuente HU:** Documento local — `docs/specs/ajustes/US-ADJ-24.md`, complementado por
  Issue [#269](https://github.com/vvalotto/cognion/issues/269)
- **Fuente Arquitectura:** `CLAUDE.md` (raíz del repo) + `docs/rf/ARQ_v1.md` + ADRs

## Historia de Usuario
- **ID:** US-ADJ-24
- **Título:** Administrador crea una Comisión
- **Tipo:** Nueva funcionalidad (frontend puro — pantalla nueva sobre endpoint ya existente)
- **Puntos:** 2
- **Prioridad:** Alta — prerrequisito de `US-ADJ-25`/`US-ADJ-26` y de la Validación E2E
  (`US-ADJ-31`)

## Decisiones de Ejecución
- **BDD:** No — es frontend puro sobre un endpoint backend ya cubierto por BDD/integración
  existentes (`test_comisiones_api_integration.py`); no hay comportamiento de dominio nuevo
  que justifique un `.feature`. Mismo criterio aplicado a otras US de frontend puro del
  proyecto (p. ej. `US-2.1.10`, `US-3.4.2`).
- **skip_bdd:** true
- **Fases a ejecutar:** 0, 2, 3, 4, 5, 7, 8, 9 (se saltan 1 y 6)

## Perfil Activo
- **Perfil:** clean-architecture-bc
- **Patrón arquitectónico:** Clean Architecture BC-First (no aplica capas de dominio en esta
  US — cambios son 100% `frontend/`)
- **Umbrales de calidad:**
  - pylint ≥ 8.0 (no aplica — sin cambios en `src/`)
  - CC ≤ 10 (no aplica — sin cambios en `src/`)
  - MI ≥ 20 (no aplica — sin cambios en `src/`)
  - cobertura ≥ 95% (Vitest, sobre los archivos frontend nuevos/modificados)

## Rutas de Artefactos
- Contexto: docs/plans/US-ADJ-24-context.md
- BDD feature: N/A (skip_bdd)
- Plan: docs/plans/US-ADJ-24-plan.md
- Reporte: docs/reports/inc4-adj/US-ADJ-24-report.md
- Quality report: quality/reports/inc4-adj/US-ADJ-24-quality.json
