# Contexto de Ejecución — US-6.2.2

## Fuentes
- **Fuente HU:** Documento local — `docs/specs/inc6/US-6.2.2.md`, GitHub Issue [#393](https://github.com/vvalotto/cognion/issues/393)
- **Fuente Arquitectura:** `CLAUDE.md` (§Arquitectura interna — reglas no negociables) + `docs/design/domain/BC-actividad-evaluativa-modelo.md` §12–§17

## Historia de Usuario
- **ID:** US-6.2.2
- **Título:** Docente muestra las opciones de la pregunta actual
- **Tipo:** Nueva funcionalidad (feature backend)
- **Puntos:** 3 (la spec no lo declara; mismo valor que el resto de la iteración)
- **Prioridad:** Alta — segundo paso manual de cada pregunta; `US-6.2.4` depende de `opciones_mostradas_en`

## Decisiones de Ejecución
- **BDD:** Sí — nueva funcionalidad con 6 escenarios Gherkin ya redactados en la spec.
- **skip_bdd:** false
- **Fases a ejecutar:** 0, 1, 2, 3, 4, 5, 6, 7, 8, 9

## Perfil Activo
- **Perfil:** clean-architecture-bc
- **Patrón arquitectónico:** clean-architecture (entities → use_cases → interface_adapters → frameworks, BC-first)
- **Umbrales de calidad:**
  - pylint ≥ 8.0 (el proyecto viene sosteniendo ≥9.0)
  - CC ≤ 10
  - MI ≥ 20
  - cobertura ≥ 95.0%

## Rutas de Artefactos
- Contexto: docs/plans/inc6/US-6.2.2-context.md
- BDD feature: tests/features/inc6/US-6.2.2-mostrar-opciones-en-vivo.feature
- Plan: docs/plans/inc6/US-6.2.2-plan.md
- Reporte: docs/reports/inc6/US-6.2.2-report.md
- Quality report: quality/reports/inc6/US-6.2.2-quality.json

## Notas específicas del proyecto (no genéricas del skill)
- Rutas de plan/contexto/reporte/quality en subcarpeta `incN/`, no en la raíz.
- Fase 7, en este orden y sin paralelizar: **1)** suite completa (`tests/`) con cobertura,
  **2)** `codeguard` con `--analysis-type full` y `PATH="$PWD/.venv/bin:$PATH"`. `designreviewer`
  con `--config pyproject.toml`.
- En zsh, expandir listas de archivos con `${=VAR}` o `$(cat archivo)`.
- Antes de cambiar la firma de un constructor (controller/use case), grepear los tests que lo
  construyen (`SesionesEnVivoController(`).
- **CBO:** `SesionesEnVivoController` pasaría a 4 use cases — verificar en Fase 2 y, si llega al
  umbral, separar por responsabilidad (`feedback_cbo_pre_push_no_fase7`).
- `tests/integration/inc6/_helpers.py` ya tiene `preparar_sesion`, `crear_estudiante` y
  `sembrar_evento_de_sesion`; reutilizar. `tests/integration/inc6/conftest.py` limpia la DB.
- **Regla de la sesión:** `tests/integration/` y BDD vacían la DB local compartida
  (`tests/uat/datos-reales/` no se commitea).
- `SesionNoEnCurso` es nueva y la reutilizan `US-6.2.4` a `US-6.2.7`.
