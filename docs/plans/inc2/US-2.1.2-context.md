# Contexto de Ejecución — US-2.1.2

## Fuentes
- **Fuente HU:** `docs/specs/inc2/US-2.1.2.md` (GitHub Issue #43)
- **Fuente Arquitectura:** `docs/rf/ARQ_v1.md` (Clean Architecture BC-first), `CLAUDE.md`

## Historia de Usuario
- **ID:** US-2.1.2
- **Título:** Comisión referencia Materia por puerto (refactor técnico)
- **Tipo:** Refactorización con cambio de comportamiento acotado (migración de datos +
  nueva validación `MateriaNoExiste` en `CrearComision`)
- **Puntos:** 3
- **Prioridad:** Alta — puede ejecutarse en paralelo o justo después de US-2.1.1 (ya cerrada,
  crea las `Materia` que esta US necesita para migrar); bloquea el resto de la Iteración 1
  solo indirectamente (no es precondición dura de US-2.1.3 a US-2.1.7)

## Decisiones de Ejecución
- **BDD:** Sí — aunque el núcleo es un refactor (`materia: str` → `materia_id: UUID`), la spec
  ya define 3 escenarios Gherkin con comportamiento observable nuevo (migración de datos,
  rechazo `MateriaNoExiste`, ausencia de imports directos entre BCs). Se formalizan como
  `.feature` en Fase 1 y se validan con step_defs de pytest-bdd en Fase 6.
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
- Contexto: docs/plans/inc2/US-2.1.2-context.md
- BDD feature: tests/features/inc2/US-2.1.2-comision-materia-port.feature
- Plan: docs/plans/inc2/US-2.1.2-plan.md
- Reporte: docs/reports/inc2/US-2.1.2-report.md
- Quality report: quality/reports/inc2/US-2.1.2-quality.json
