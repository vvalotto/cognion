# Contexto de Ejecución — US-6.2.6

## Fuentes
- **Fuente HU:** Documento local — `docs/specs/inc6/US-6.2.6.md`, GitHub Issue [#397](https://github.com/vvalotto/cognion/issues/397)
- **Fuente Arquitectura:** `CLAUDE.md` (§Arquitectura interna — reglas no negociables) + `docs/design/domain/BC-actividad-evaluativa-modelo.md` §12–§17

## Historia de Usuario
- **ID:** US-6.2.6
- **Título:** Docente avanza a la siguiente pregunta
- **Tipo:** Nueva funcionalidad (feature backend)
- **Puntos:** 3 (la spec no lo declara; transición de estado simple, mismo patrón que US-6.1.4)
- **Prioridad:** Alta — segundo paso del "avance en dos pasos"; `US-6.2.7` y `US-6.2.9` dependen de ella

## Decisiones de Ejecución
- **BDD:** Sí — nueva funcionalidad con 7 escenarios Gherkin ya redactados en la spec.
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
- Contexto: docs/plans/inc6/US-6.2.6-context.md
- BDD feature: tests/features/inc6/US-6.2.6-avanzar-siguiente-pregunta.feature
- Plan: docs/plans/inc6/US-6.2.6-plan.md
- Reporte: docs/reports/inc6/US-6.2.6-report.md
- Quality report: quality/reports/inc6/US-6.2.6-quality.json

## Notas específicas del proyecto (no genéricas del skill)
- Rutas de plan/contexto/reporte/quality en subcarpeta `incN/`.
- Fase 7, en orden y sin paralelizar: 1) suite completa con cobertura, 2) `codeguard --analysis-type full`
  con `PATH="$PWD/.venv/bin:$PATH"`. `designreviewer` con `--config pyproject.toml`.
- En zsh, expandir listas de archivos con `${=VAR}` o `$(cat archivo)`.
- Antes de cambiar la firma de un constructor, grepear los tests que lo construyen.
- **CBO:** `avanzar_siguiente_pregunta` va en `ConduccionEnVivoController` (ya separado de
  `SesionesEnVivoController`); vigilar CBO al sumar el use case ahí.
- **Reutilización:** extraer el armado del mensaje `pregunta_presentada` de
  `iniciar_sesion_en_vivo.py` a una función compartida, no duplicarlo.
- **Regla de la sesión:** `tests/integration/` y BDD vacían la DB local compartida.
- Integración: incluir el mensaje completo a dos WebSockets conectados.
