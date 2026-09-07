# Contexto de Ejecución — US-ADJ-23

## Fuentes
- **Fuente HU:** `docs/specs/ajustes/US-ADJ-23.md`
- **Fuente Arquitectura:** `docs/rf/ARQ_v1.md`, `CLAUDE.md` §"Arquitectura interna" (Clean
  Architecture BC-first, ya decidida — no se pregunta por stack/arquitectura)

## Historia de Usuario
- **ID:** US-ADJ-23
- **Título:** Administrador ve el listado de Comisiones de una Materia
- **Tipo:** Nueva funcionalidad
- **Puntos:** 3
- **Prioridad:** Alta — precondición de `US-ADJ-24`/`25`/`26` (alta de Estudiante real vía UI)

## Decisiones de Ejecución
- **BDD:** Sí — nueva funcionalidad (pantalla + ampliación de permiso de lectura)
- **skip_bdd:** false
- **Fases a ejecutar:** 0, 1, 2, 3, 4, 5, 6, 7, 8, 9

## Perfil Activo
- **Perfil:** `clean-architecture-bc`
- **Patrón arquitectónico:** Clean Architecture BC-first (entities → use_cases →
  interface_adapters → frameworks)
- **Umbrales de calidad:**
  - pylint ≥ 8.0
  - CC ≤ 10
  - MI ≥ 20
  - cobertura ≥ 95%

## Rutas de Artefactos
- Contexto: `docs/plans/inc4-adj/US-ADJ-23-context.md`
- BDD feature: `tests/features/inc4-adj/US-ADJ-23-listado-comisiones.feature`
- Plan: `docs/plans/inc4-adj/US-ADJ-23-plan.md`
- Reporte: `docs/reports/inc4-adj/US-ADJ-23-report.md`
- Quality report: `quality/reports/inc4-adj/US-ADJ-23-quality.json`
