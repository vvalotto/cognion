# Contexto de Ejecución — US-6.2.5

## Fuentes
- **Fuente HU:** Documento local — `docs/specs/inc6/US-6.2.5.md`, GitHub Issue [#396](https://github.com/vvalotto/cognion/issues/396)
- **Fuente Arquitectura:** `CLAUDE.md` (§Arquitectura interna — reglas no negociables) + `docs/design/domain/BC-actividad-evaluativa-modelo.md` §12–§17

## Historia de Usuario
- **ID:** US-6.2.5
- **Título:** Docente cierra la pregunta actual en vivo
- **Tipo:** Nueva funcionalidad (feature backend)
- **Puntos:** 5 (la spec no lo declara; mismo peso que 6.2.2/6.2.4)
- **Prioridad:** Alta — cierre del ciclo de una pregunta (RF-09, primer RNF de rendimiento en juego); `US-6.2.6`, `6.2.7` y `6.2.9` dependen de ella

## Decisiones de Ejecución
- **BDD:** Sí — nueva funcionalidad con 9 escenarios Gherkin ya redactados en la spec.
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
- Contexto: docs/plans/inc6/US-6.2.5-context.md
- BDD feature: tests/features/inc6/US-6.2.5-cerrar-pregunta-en-vivo.feature
- Plan: docs/plans/inc6/US-6.2.5-plan.md
- Reporte: docs/reports/inc6/US-6.2.5-report.md
- Quality report: quality/reports/inc6/US-6.2.5-quality.json

## Notas específicas del proyecto (no genéricas del skill)
- Rutas de plan/contexto/reporte/quality en subcarpeta `incN/`.
- Fase 7, en orden y sin paralelizar: 1) suite completa con cobertura, 2) `codeguard --analysis-type full`
  con `PATH="$PWD/.venv/bin:$PATH"`. `designreviewer` con `--config pyproject.toml`.
- En zsh, expandir listas de archivos con `${=VAR}` o `$(cat archivo)`.
- Antes de cambiar la firma de un constructor, grepear los tests que lo construyen.
- **CBO:** el use case depende de event store, proyecciones (solo lectura), `PreguntaConsultaPort`
  y canal — vigilar CBO. El controller ya está separado: `mostrar_opciones` se movió a
  `ConduccionEnVivoController` (commit `992b0ea`), donde va `cerrar_pregunta`.
- **RNF:** no agregar trabajo pesado en el camino del cierre (solo lectura de proyecciones + un
  único broadcast); la medición formal es `US-6.2.9`.
- Reutilizar `tests/integration/inc6/_helpers.py` y `conftest.py` (limpia la DB).
- **Regla de la sesión:** `tests/integration/` y BDD vacían la DB local compartida.
- Integración: incluir el mensaje completo a dos WebSockets conectados.
