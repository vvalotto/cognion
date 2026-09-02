# Contexto de Ejecución — US-3.3.2

## Fuentes
- **Fuente HU:** GitHub Issue [#164](https://github.com/vvalotto/cognion/issues/164) + spec
  `docs/specs/inc3/US-3.3.2.md` (ya redactada) + `docs/plans/inc3/inc3-candidatas.md`
  (Iteración 3) + `docs/design/domain/BC-actividad-evaluativa-modelo.md` §3/§4/§5/§6b (Regla 3)
- **Fuente Arquitectura:** `docs/rf/ARQ_v1.md`, `CLAUDE.md` (reglas de capas Clean Architecture
  BC-first), código existente de `src/actividad_evaluativa/` (US-3.1.1 a US-3.3.1 ya establecen
  el patrón de event store + Unit of Work por Use Case + read model de evaluaciones activas +
  `reconstruir()` sobre `ActividadEvaluativaPeriodoAbierto`)

## Historia de Usuario
- **ID:** US-3.3.2
- **Título:** Docente cierra una actividad manualmente antes de tiempo
- **Tipo:** Nueva funcionalidad — implementa la Regla 3 del `VerificadorDeVencimientos`
  (cascada síncrona, no vía Policy periódica)
- **Puntos:** 5
- **Prioridad:** Alta — RF-11b (medida opcional), cierra la Iteración 3 del Incremento 3
  (backend)

## Decisiones de Ejecución
- **BDD:** Sí — comportamiento observable de negocio (cierre manual, cascada de finalización,
  terminalidad INV-AE-04b), no es refactor puro.
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
- Contexto: docs/plans/inc3/US-3.3.2-context.md
- BDD feature: tests/features/inc3/US-3.3.2-cerrar-actividad.feature
- Plan: docs/plans/inc3/US-3.3.2-plan.md
- Reporte: docs/reports/inc3/US-3.3.2-report.md
- Quality report: quality/reports/inc3/US-3.3.2-quality.json
- Spec: docs/specs/inc3/US-3.3.2.md (ya redactada, previa a esta ejecución)
