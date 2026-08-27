# Contexto de Ejecución — US-3.2.4

## Fuentes
- **Fuente HU:** GitHub Issue [#159](https://github.com/vvalotto/cognion/issues/159) + `docs/plans/inc3/inc3-candidatas.md` (Iteración 2) + `docs/design/domain/BC-actividad-evaluativa-modelo.md` §6b (`VerificadorDeVencimientos`)
- **Fuente Arquitectura:** `docs/rf/ARQ_v1.md`, `CLAUDE.md` (reglas de capas Clean Architecture BC-first), código existente de `src/actividad_evaluativa/` (US-3.1.1 a US-3.2.3, ya establece el patrón de event store + Unit of Work por Use Case)

## Historia de Usuario
- **ID:** US-3.2.4
- **Título:** VerificadorDeVencimientos — suspensión y finalización automáticas
- **Tipo:** Técnica (Policy/Process Manager) — extiende comportamiento existente (Reglas 1/2 sobre `SuspenderEvaluacion`/`FinalizarEvaluacion` ya implementadas en US-3.2.2/US-3.2.3) + infraestructura nueva (read model)
- **Puntos:** 5
- **Prioridad:** Alta — cierra la Iteración 2 del Incremento 3 (backend)

## Decisiones de Ejecución
- **BDD:** Sí — hay comportamiento observable de negocio (reglas 1 y 2 disparan transiciones de estado con actor `sistema`, idempotencia verificable), no es refactor puro.
- **skip_bdd:** false
- **Fases a ejecutar:** 0, 1, 2, 3, 4, 5, 6, 7, 8, 9

## Perfil Activo
- **Perfil:** clean-architecture-bc
- **Patrón arquitectónico:** Clean Architecture BC-first (entities → use_cases → interface_adapters → frameworks)
- **Umbrales de calidad:**
  - pylint ≥ 8.0
  - CC ≤ 10
  - MI ≥ 20
  - cobertura ≥ 95%

## Rutas de Artefactos
- Contexto: docs/plans/inc3/US-3.2.4-context.md
- BDD feature: tests/features/inc3/US-3.2.4-verificador-vencimientos.feature
- Plan: docs/plans/inc3/US-3.2.4-plan.md
- Reporte: docs/reports/inc3/US-3.2.4-report.md
- Quality report: quality/reports/inc3/US-3.2.4-quality.json
- Spec: docs/specs/inc3/US-3.2.4.md (a redactar en Fase 2, antes del plan — no existe todavía)
