# Contexto de Ejecución — US-6.1.4

## Fuentes
- **Fuente HU:** Documento local — `docs/specs/inc6/US-6.1.4.md`, GitHub Issue [#385](https://github.com/vvalotto/cognion/issues/385)
- **Fuente Arquitectura:** `CLAUDE.md` (§Arquitectura interna — reglas no negociables) + `docs/design/domain/BC-actividad-evaluativa-modelo.md` §12–§17

## Historia de Usuario
- **ID:** US-6.1.4
- **Título:** Docente inicia la sesión en vivo — se presenta la primera pregunta
- **Tipo:** Nueva funcionalidad (feature backend)
- **Puntos:** 3 (la spec no lo declara; mismo valor que el resto de la iteración)
- **Prioridad:** Alta — cierra la Iteración 1 del Incremento 6

## Decisiones de Ejecución
- **BDD:** Sí — nueva funcionalidad con 5 escenarios Gherkin ya redactados en la spec.
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
- Contexto: docs/plans/inc6/US-6.1.4-context.md
- BDD feature: tests/features/inc6/US-6.1.4-iniciar-sesion-en-vivo.feature
- Plan: docs/plans/inc6/US-6.1.4-plan.md
- Reporte: docs/reports/inc6/US-6.1.4-report.md
- Quality report: quality/reports/inc6/US-6.1.4-quality.json

## Notas específicas del proyecto (no genéricas del skill)
- Rutas de plan/contexto/reporte/quality en subcarpeta `incN/`, no en la raíz.
- Fase 7, en este orden y sin paralelizar: **1)** suite completa (`tests/`) con cobertura,
  **2)** `codeguard` con `--analysis-type full` y `PATH="$PWD/.venv/bin:$PATH"`. `designreviewer`
  con `--config pyproject.toml`.
- En zsh, expandir listas de archivos con `${=VAR}` o `$(cat archivo)`, y no guardar un comando
  con argumentos en una variable.
- Antes de cambiar la firma de un constructor (controller/use case), grepear los tests que lo
  construyen (`SesionesEnVivoController(` ya rompió un test de la US anterior).
- `tests/integration/inc6/_helpers.py` ya tiene `preparar_sesion`, `crear_estudiante` y
  `sembrar_evento_de_sesion`; reutilizar. `tests/integration/inc6/conftest.py` limpia la DB.
- **Puntos de diseño para Fase 2:** (1) la spec pide `tipo` en el payload de
  `SesionEnVivoIniciada`, pero `PreguntaConsultaPort.obtener_contenido()` hoy solo devuelve
  `texto` y `opciones`; (2) `reconstruir()` ya trata `SesionEnVivoIniciada` como `EnCurso`
  (sembrado en `US-6.1.3`) — ahora hay un payload real y hay que fijar `pregunta_actual_indice`;
  (3) los tests de `US-6.1.3` que siembran ese evento a mano pueden usar el endpoint real.
- `tests/uat/datos-reales/` y los trackers no se commitean.
