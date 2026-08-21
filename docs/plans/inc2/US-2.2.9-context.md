# Contexto de Ejecución — US-2.2.9

## Fuentes
- **Fuente HU:** Documento local — `docs/specs/inc2/US-2.2.9.md` (Issue GitHub #104)
- **Fuente Arquitectura:** `docs/rf/ARQ_v1.md` + `CLAUDE.md` (Clean Architecture BC-first)

## Historia de Usuario
- **ID:** US-2.2.9
- **Título:** Login refleja el estado de cuenta bloqueada (UI)
- **Tipo:** Mejora de comportamiento existente (frontend)
- **Puntos:** 2
- **Prioridad:** Alta — última US de la Iteración 2

## Decisiones de Ejecución
- **BDD:** Sí — extiende el flujo de login (`US-1.1.7`) con una rama de error nueva y
  observable por el usuario; ya existe `.feature` de referencia para el patrón (`US-2.2.8`).
- **skip_bdd:** false
- **Fases a ejecutar:** 0, 1, 2, 3, 4, 5, 6, 7, 8, 9

## Perfil Activo
- **Perfil:** clean-architecture-bc
- **Patrón arquitectónico:** clean-architecture (BC-first)
- **Umbrales de calidad:**
  - pylint ≥ 8.0
  - CC ≤ 10
  - MI ≥ 20
  - cobertura ≥ 95%

## Alcance
- **Backend:** sin cambios — `US-2.2.1` ya distingue `CuentaBloqueadaError` con 403.
- **Frontend:** `frontend/src/lib/auth-api.ts` (distinguir código de error de cuenta
  bloqueada), `frontend/src/pages/Login.tsx` (alerta específica + formulario deshabilitado).

## Rutas de Artefactos
- Contexto: docs/plans/inc2/US-2.2.9-context.md
- BDD feature: tests/features/inc2/US-2.2.9-login-cuenta-bloqueada.feature
- Plan: docs/plans/inc2/US-2.2.9-plan.md
- Reporte: docs/reports/inc2/US-2.2.9-report.md
- Quality report: quality/reports/inc2/US-2.2.9-quality.json
