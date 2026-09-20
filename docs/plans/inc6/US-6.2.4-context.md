# Contexto de Ejecución — US-6.2.4

## Fuentes
- **Fuente HU:** Documento local — `docs/specs/inc6/US-6.2.4.md`, GitHub Issue [#395](https://github.com/vvalotto/cognion/issues/395)
- **Fuente Arquitectura:** `CLAUDE.md` (§Arquitectura interna — reglas no negociables) + `docs/design/domain/BC-actividad-evaluativa-modelo.md` §12–§17

## Historia de Usuario
- **ID:** US-6.2.4
- **Título:** Estudiante responde una pregunta en vivo
- **Tipo:** Nueva funcionalidad (feature backend)
- **Puntos:** 5 (la spec no lo declara; estimación por ser el núcleo de RF-09/RF-10)
- **Prioridad:** Alta — núcleo de RF-09/RF-10; `US-6.2.5` depende de ella

## Decisiones de Ejecución
- **BDD:** Sí — nueva funcionalidad con 11 escenarios Gherkin ya redactados en la spec.
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
- Contexto: docs/plans/inc6/US-6.2.4-context.md
- BDD feature: tests/features/inc6/US-6.2.4-responder-pregunta-en-vivo.feature
- Plan: docs/plans/inc6/US-6.2.4-plan.md
- Reporte: docs/reports/inc6/US-6.2.4-report.md
- Quality report: quality/reports/inc6/US-6.2.4-quality.json

## Notas específicas del proyecto (no genéricas del skill)
- Rutas de plan/contexto/reporte/quality en subcarpeta `incN/`.
- Fase 7, en orden y sin paralelizar: 1) suite completa con cobertura, 2) `codeguard --analysis-type full`
  con `PATH="$PWD/.venv/bin:$PATH"`. `designreviewer` con `--config pyproject.toml`.
- En zsh, expandir listas de archivos con `${=VAR}` o `$(cat archivo)`.
- Antes de cambiar la firma de un constructor, grepear los tests que lo construyen.
- **CBO:** el use case tiene muchas dependencias (sesión, PreguntaConsultaPort, proyecciones
  escritura/lectura, canal) y el controller ya tiene 4-5 use cases — evaluar controller propio en Fase 2.
- Reutilizar `tests/integration/inc6/_helpers.py` y `conftest.py` (limpia la DB).
- **Regla de la sesión:** `tests/integration/` y BDD vacían la DB local compartida.
- Concurrencia real (60 respuestas simultáneas y doble envío) contra la DB en integración.
