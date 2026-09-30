# Contexto de Ejecución — US-6.2.8

## Fuentes
- **Fuente HU:** Documento local — `docs/specs/inc6/US-6.2.8.md`, GitHub Issue [#399](https://github.com/vvalotto/cognion/issues/399)
- **Fuente Arquitectura:** `CLAUDE.md` (§Arquitectura interna — reglas no negociables) + `docs/design/domain/BC-actividad-evaluativa-modelo.md` §12–§17

## Historia de Usuario
- **ID:** US-6.2.8
- **Título:** Consultar el estado de la sesión, sus participantes y su ranking
- **Tipo:** Nueva funcionalidad (feature backend — consultas, sin comando ni evento)
- **Puntos:** 3 (la spec no lo declara; transición de estado simple, mismo patrón que US-6.1.4)
- **Prioridad:** Alta — habilita reconexión y sala de espera; `US-6.2.9` depende de ella

## Decisiones de Ejecución
- **BDD:** Sí — nueva funcionalidad con 10 escenarios Gherkin ya redactados en la spec.
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
- Contexto: docs/plans/inc6/US-6.2.8-context.md
- BDD feature: tests/features/inc6/US-6.2.8-consultar-estado-sesion-en-vivo.feature
- Plan: docs/plans/inc6/US-6.2.8-plan.md
- Reporte: docs/reports/inc6/US-6.2.8-report.md
- Quality report: quality/reports/inc6/US-6.2.8-quality.json

## Notas específicas del proyecto (no genéricas del skill)
- Rutas de plan/contexto/reporte/quality en subcarpeta `incN/`.
- Fase 7, en orden y sin paralelizar: 1) suite completa con cobertura, 2) `codeguard --analysis-type full`
  con `PATH="$PWD/.venv/bin:$PATH"`. `designreviewer` con `--config pyproject.toml`.
- **`git add` solo de rutas concretas**: nunca `git add tests` — arrastra `tests/uat/datos-reales/`.
- Editar planes/specs con Python (`sed -i` con `#` falla en macOS/zsh); `tracker_cli.py` invocado directo.
- **CBO:** controller de consultas propio (`SesionesEnVivoQueryController`), separado de los de comandos.
- **Regla de la sesión:** `tests/integration/` y BDD vacían la DB local compartida.
- Nunca exponer la respuesta correcta antes de cerrar la pregunta; opciones solo si `opciones_mostradas`.
