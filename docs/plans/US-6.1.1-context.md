# Contexto de Ejecución — US-6.1.1

## Fuentes
- **Fuente HU:** Documento local — `docs/specs/inc6/US-6.1.1.md` (spec ya escrita y aprobada en `docs/plans/inc6/inc6-candidatas.md`), GitHub Issue [#382](https://github.com/vvalotto/cognion/issues/382)
- **Fuente Arquitectura:** `CLAUDE.md` (§Arquitectura interna — reglas no negociables) + `docs/design/domain/BC-actividad-evaluativa-modelo.md` §14, §16, §17 punto 11

## Historia de Usuario
- **ID:** US-6.1.1
- **Título:** Infraestructura de tiempo real (WebSockets) y ComisionConsultaPort de Actividad Evaluativa
- **Tipo:** Infraestructura técnica, sin comando de negocio propio
- **Puntos:** 3
- **Prioridad:** Alta — bloquea el resto de la Iteración 1 (`US-6.1.2` a `US-6.1.4`)

## Decisiones de Ejecución
- **BDD:** No — mismo precedente que `US-3.1.1` (`docs/reports/inc3/US-3.1.1-report.md`:
  `skip_bdd: true` por decisión de Víctor, escenarios Gherkin de la spec documentados pero
  cubiertos por tests de integración uno a uno, sin formalizar como `.feature`). Esta US replica
  ese criterio: los 6 escenarios de `docs/specs/inc6/US-6.1.1.md` quedan como especificación de
  los tests de integración/unitarios de Fase 4/5, no como `.feature` de Fase 1/6.
- **skip_bdd:** true
- **Fases a ejecutar:** 0, 2, 3, 4, 5, 7, 8, 9 (se saltean 1 y 6)

## Perfil Activo
- **Perfil:** clean-architecture-bc
- **Patrón arquitectónico:** clean-architecture (entities → use_cases → interface_adapters → frameworks, BC-first)
- **Umbrales de calidad:**
  - pylint ≥ 8.0 (umbral del skill; el proyecto viene sosteniendo ≥9.0 en US recientes)
  - CC ≤ 10
  - MI ≥ 20 (umbral del skill; el proyecto viene sosteniendo ≥40 en US recientes)
  - cobertura ≥ 95.0%

## Rutas de Artefactos
- Contexto: docs/plans/US-6.1.1-context.md
- BDD feature: tests/features/inc6/US-6.1.1.feature
- Plan: docs/plans/US-6.1.1-plan.md
- Reporte: docs/reports/inc6/US-6.1.1-report.md
- Quality report: quality/reports/inc6/US-6.1.1-quality.json

## Notas específicas del proyecto (no genéricas del skill)
- Rutas de reporte/quality van en subcarpeta `incN/` (`docs/reports/inc6/`,
  `quality/reports/inc6/`), no en la raíz de `docs/reports/`/`quality/reports/` —
  convención de Cognión, no del template genérico del skill.
- `CodeGuard` en Fase 7 debe correr con `--analysis-type full` (no el default `pre-commit`),
  por el fix de proceso de `US-ADJ` post-`BL-010` (`CLAUDE.md` §Quality gates).
- `designreviewer` siempre con `--config pyproject.toml`.
- No correr `pytest` contra la base de datos local mientras haya datos de la prueba manual de
  estabilización en curso (`tests/uat/datos-reales/`, sin US-IEDD) — no aplica a esta sesión
  porque esa prueba ya cerró (`BL-008`), pero se deja registrado por si hay overlap.
