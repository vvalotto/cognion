# Contexto de Ejecución — US-ADJ-48

## Fuentes
- **Fuente HU:** Documento local — `docs/specs/ajustes/US-ADJ-48.md`
- **Fuente Arquitectura:** `CLAUDE.md` (reglas de capas) + `docs/design/ux/wireframes-analytics.md` §3.2/§4 — sin capas de dominio aplicables (frontend puro)

## Historia de Usuario
- **ID:** US-ADJ-48
- **Título:** Docente ve "Desempeño por comisión" con drill-down
- **Tipo:** Nueva funcionalidad (frontend puro, consume backend ya cerrado en `US-ADJ-44`)
- **Puntos:** 5 (sin asignación formal, mismo criterio que el resto de Analytics)
- **Prioridad:** Primera US de la Iteración 4 frontend del Incremento 5-ADJ — par backend→frontend de RF-20

## Decisiones de Ejecución
- **BDD:** No — frontend puro sobre pantallas nuevas, sin lógica de dominio backend; criterios de aceptación son interacción de UI (selección Materia→Comisión, tabla, dos niveles de drill-down, RBAC), verificables con Vitest + Testing Library. El proyecto no tiene infraestructura BDD para frontend — los `.feature`/pytest-bdd se usan solo para backend. Mismo criterio aplicado en `US-ADJ-35`/`36`/`37`.
- **skip_bdd:** true
- **Fases a ejecutar:** 0, 2, 3, 4, 5, 7, 8, 9 (se omiten 1 y 6)

## Perfil Activo
- **Perfil:** clean-architecture-bc
- **Patrón arquitectónico:** clean-architecture (no aplica a esta US — frontend puro, sin capas entities/use_cases/interface_adapters/frameworks)
- **Umbrales de calidad:**
  - pylint ≥ 8.0 (N/A — sin código Python en esta US)
  - CC ≤ 10 (N/A)
  - MI ≥ 20 (N/A)
  - cobertura ≥ 95% (aplica a `frontend/`, vía Vitest — umbral de branches del proyecto: 80% global, ver `CLAUDE.md`/`US-ADJ-16`)

## Rutas de Artefactos
- Contexto: docs/plans/inc5-adj/US-ADJ-48-context.md
- BDD feature: N/A (skip_bdd)
- Plan: docs/plans/inc5-adj/US-ADJ-48-plan.md
- Reporte: docs/reports/inc5-adj/US-ADJ-48-report.md
- Quality report: quality/reports/inc5-adj/US-ADJ-48-quality.json
