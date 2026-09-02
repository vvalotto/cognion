# Contexto de Ejecución — US-3.3.1

## Fuentes
- **Fuente HU:** GitHub Issue [#163](https://github.com/vvalotto/cognion/issues/163) + spec
  `docs/specs/inc3/US-3.3.1.md` (ya redactada) + `docs/plans/inc3/inc3-candidatas.md`
  (Iteración 3) + `docs/design/domain/BC-actividad-evaluativa-modelo.md` §4/§5/§9
- **Fuente Arquitectura:** `docs/rf/ARQ_v1.md`, `CLAUDE.md` (reglas de capas Clean Architecture
  BC-first), código existente de `src/actividad_evaluativa/` (US-3.1.1 a US-3.2.4 ya establecen
  el patrón de event store + Unit of Work por Use Case + read model de evaluaciones activas)

## Historia de Usuario
- **ID:** US-3.3.1
- **Título:** Docente extiende (o intenta acortar) el plazo de una actividad vigente
- **Tipo:** Nueva funcionalidad — primer comando que agrega un segundo evento al stream de
  `ActividadEvaluativaPeriodoAbierto` (introduce `reconstruir()` real sobre ese aggregate)
- **Puntos:** 5
- **Prioridad:** Alta — RF-11b, primera US de la Iteración 3 del Incremento 3 (backend)

## Decisiones de Ejecución
- **BDD:** Sí — comportamiento observable de negocio (extender siempre permitido, acortar
  condicionado a INV-AE-04, rechazo terminal por INV-AE-04b), no es refactor puro.
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
- Contexto: docs/plans/inc3/US-3.3.1-context.md
- BDD feature: tests/features/inc3/US-3.3.1-modificar-periodo-disponibilidad.feature
- Plan: docs/plans/inc3/US-3.3.1-plan.md
- Reporte: docs/reports/inc3/US-3.3.1-report.md
- Quality report: quality/reports/inc3/US-3.3.1-quality.json
- Spec: docs/specs/inc3/US-3.3.1.md (ya redactada, previa a esta ejecución — a diferencia de
  US-3.2.4, donde la spec se redactaba en Fase 2)
