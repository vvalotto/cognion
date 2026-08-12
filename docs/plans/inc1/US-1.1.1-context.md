# Contexto de Ejecución — US-1.1.1

## Fuentes
- **Fuente HU:** `docs/specs/inc1/US-1.1.1.md` (Issue GitHub #6)
- **Fuente Arquitectura:** `docs/rf/ARQ_v1.md` + `CLAUDE.md` (Clean Architecture BC-first)

## Historia de Usuario
- **ID:** US-1.1.1
- **Título:** Docente genera link de invitación para una comisión
- **Tipo:** Nueva funcionalidad
- **Puntos:** 3
- **Prioridad:** Alta — precondición de US-1.1.2/US-1.1.3 (registro de Estudiante por invitación)

## Decisión de alcance — dependencia de JWT (US-1.1.4)

La spec exige "Actor autenticado con JWT válido y claim `rol = docente`" como precondición,
pero `US-1.1.4` (login/JWT) todavía no está implementada — no existe middleware de auth en
el código (`git grep` sobre `src/identidad` no encontró ningún módulo de JWT/sesión).

**Decisión (confirmada por Víctor):** el endpoint recibe `docente_id` explícito en el
body/path — mismo patrón que `POST /comisiones/{id}/docentes` de US-1.1.0 — sin validar JWT
todavía. INV-ID-08 (`docente_id` ∈ `docentes_asignados`) se valida igual, a nivel de use
case, independientemente del mecanismo de autenticación. Cuando se implemente `US-1.1.4`, el
guard de JWT se agrega como capa adicional (dependency de FastAPI) sin tocar el use case.

## Decisiones de Ejecución
- **BDD:** Sí — nueva funcionalidad con criterios de aceptación Gherkin ya definidos en la spec
- **skip_bdd:** false
- **Fases a ejecutar:** 0, 1, 2, 3, 4, 5, 6, 7, 8, 9

## Perfil Activo
- **Perfil:** clean-architecture-bc
- **Patrón arquitectónico:** clean-architecture (entities → use_cases → interface_adapters → frameworks, BC-first)
- **Umbrales de calidad:**
  - pylint ≥ 8.0
  - CC ≤ 10
  - MI ≥ 20
  - cobertura ≥ 95%

## Rutas de Artefactos
- Contexto: docs/plans/inc1/US-1.1.1-context.md
- BDD feature: tests/features/inc1/US-1.1.1-generar-invitacion.feature
- Plan: docs/plans/inc1/US-1.1.1-plan.md
- Reporte: docs/reports/inc1/US-1.1.1-report.md
- Quality report: quality/reports/inc1/US-1.1.1-quality.json
