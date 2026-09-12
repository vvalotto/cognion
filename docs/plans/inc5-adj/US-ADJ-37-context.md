# Contexto de Ejecución — US-ADJ-37

## Fuentes
- **Fuente HU:** Documento local — `docs/specs/ajustes/US-ADJ-37.md`
- **Fuente Arquitectura:** Archivo local — `docs/rf/ARQ_v1.md` + `CLAUDE.md` (reglas de capas), sin capas de dominio aplicables (frontend puro)

## Historia de Usuario
- **ID:** US-ADJ-37
- **Título:** Descubribilidad — Cambiar contraseña y Cerrar sesión en el menú
- **Tipo:** Mejora de comportamiento existente (nuevo punto de entrada UI a funciones ya implementadas)
- **Puntos:** 1
- **Prioridad:** Última US de la Iteración 1 del Incremento 5-ADJ — la cierra completa

## Decisiones de Ejecución
- **BDD:** No — frontend puro sobre un componente de layout (`AppLayout.tsx`), sin lógica de dominio backend; criterios de aceptación son interacción de UI (abrir menú, navegar, limpiar sesión), verificables con Vitest + Testing Library sin necesidad de step definitions Gherkin/pytest-bdd (el proyecto no tiene infraestructura BDD para frontend — los `.feature`/pytest-bdd se usan para backend). Mismo criterio aplicado en `US-ADJ-35`/`US-ADJ-36` (frontend puro, sin BDD).
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
- Contexto: docs/plans/inc5-adj/US-ADJ-37-context.md
- BDD feature: N/A (skip_bdd)
- Plan: docs/plans/inc5-adj/US-ADJ-37-plan.md
- Reporte: docs/reports/inc5-adj/US-ADJ-37-report.md
- Quality report: quality/reports/inc5-adj/US-ADJ-37-quality.json
