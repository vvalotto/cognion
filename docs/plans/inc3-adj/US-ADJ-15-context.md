# Contexto de Ejecución — US-ADJ-15

## Fuentes
- **Fuente HU:** Documento local — `docs/specs/ajustes/US-ADJ-15.md`
- **Fuente Arquitectura:** `docs/rf/ARQ_v1.md` + `CLAUDE.md` (Clean Architecture interna,
  perfil `clean-architecture-bc`) — no aplica al cambio en sí (config de una herramienta de
  calidad, transversal, no toca `src/`)

## Historia de Usuario
- **ID:** US-ADJ-15
- **Título:** Fix de `coverage_report_path` en `[tool.architectanalyst]`
- **Tipo:** Config (una línea, ya verificada en la investigación previa a la spec)
- **Puntos:** 1
- **Prioridad:** Media (warning vacío repetido en 3 baselines, `CoverageAnalyzer` sin aportar
  dato real)

## Decisiones de Ejecución
- **BDD:** No — config de una línea sin comportamiento de dominio ni de aplicación.
- **skip_bdd:** true
- **Fases a ejecutar:** 0, 2, 3, 8, 9 (se saltan 1, 4, 5, 6 y 7 — sin código de producción;
  verificación directa en Fase 3: generar `coverage.json` y correr `architectanalyst`)

## Perfil Activo
- **Perfil:** `clean-architecture-bc`
- **Patrón arquitectónico:** N/A — config transversal de tooling
- **Umbrales de calidad:** N/A. Verificación de aceptación: `architectanalyst src/ --config
  pyproject.toml` (corrido después de generar `coverage.json` en la raíz) reporta
  `CoverageAnalyzer` en `info` con el porcentaje real, no en `warning`.

## Rutas de Artefactos
- Contexto: `docs/plans/inc3-adj/US-ADJ-15-context.md`
- BDD feature: N/A (skip_bdd)
- Plan: `docs/plans/inc3-adj/US-ADJ-15-plan.md`
- Reporte: `docs/reports/inc3-adj/US-ADJ-15-report.md`
- Quality report: `quality/reports/inc3-adj/US-ADJ-15-quality.json`
