# Contexto de Ejecución — US-6.1.2

## Fuentes
- **Fuente HU:** Documento local — `docs/specs/inc6/US-6.1.2.md`, GitHub Issue [#383](https://github.com/vvalotto/cognion/issues/383)
- **Fuente Arquitectura:** `CLAUDE.md` (§Arquitectura interna — reglas no negociables) + `docs/design/domain/BC-actividad-evaluativa-modelo.md` §12–§14, §17 punto 11

## Historia de Usuario
- **ID:** US-6.1.2
- **Título:** Docente crea una sesión en vivo desde el detalle de una Comisión
- **Tipo:** Nueva funcionalidad (feature backend)
- **Puntos:** 3
- **Prioridad:** Alta — bloquea `US-6.1.3` y `US-6.1.4`

## Decisiones de Ejecución
- **BDD:** Sí — nueva funcionalidad con 5 escenarios Gherkin ya redactados en la spec
  (precedente: `US-3.1.2`, `US-3.1.3`).
- **skip_bdd:** false
- **Fases a ejecutar:** 0, 1, 2, 3, 4, 5, 6, 7, 8, 9

## Perfil Activo
- **Perfil:** clean-architecture-bc
- **Patrón arquitectónico:** clean-architecture (entities → use_cases → interface_adapters → frameworks, BC-first)
- **Umbrales de calidad:**
  - pylint ≥ 8.0 (umbral del skill; el proyecto viene sosteniendo ≥9.0 en US recientes)
  - CC ≤ 10
  - MI ≥ 20 (umbral del skill; el proyecto viene sosteniendo ≥40 en US recientes)
  - cobertura ≥ 95.0%

## Rutas de Artefactos
- Contexto: docs/plans/inc6/US-6.1.2-context.md
- BDD feature: tests/features/inc6/US-6.1.2.feature
- Plan: docs/plans/inc6/US-6.1.2-plan.md
- Reporte: docs/reports/inc6/US-6.1.2-report.md
- Quality report: quality/reports/inc6/US-6.1.2-quality.json

## Notas específicas del proyecto (no genéricas del skill)
- Rutas de plan/contexto/reporte/quality van en subcarpeta `incN/` (`docs/plans/inc6/`,
  `docs/reports/inc6/`, `quality/reports/inc6/`), no en la raíz.
- `CodeGuard` en Fase 7 con `--analysis-type full` (no el default `pre-commit`).
- `designreviewer` siempre con `--config pyproject.toml`.
- CBO: `SesionesEnVivoController` es nuevo y separado, no extender `ActividadesController`
  (ya cerca del umbral 10/10) — detectarlo en Fase 2.
- Precedente de aggregate ES + set sampleado: `CrearActividadPeriodoAbierto` (`US-3.1.2`) e
  `IniciarEvaluacion` (`US-3.1.3`).
- Depende de `ComisionConsultaPort` y `sesiones_en_vivo_router.py` de `US-6.1.1`.
