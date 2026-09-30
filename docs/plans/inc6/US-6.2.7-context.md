# Contexto de Ejecución — US-6.2.7

## Fuentes
- **Fuente HU:** Documento local — `docs/specs/inc6/US-6.2.7.md`, GitHub Issue [#398](https://github.com/vvalotto/cognion/issues/398)
- **Fuente Arquitectura:** `CLAUDE.md` (§Arquitectura interna — reglas no negociables) + `docs/design/domain/BC-actividad-evaluativa-modelo.md` §12–§17

## Historia de Usuario
- **ID:** US-6.2.7
- **Título:** Docente finaliza la sesión — ranking final
- **Tipo:** Nueva funcionalidad (feature backend)
- **Puntos:** 3 (la spec no lo declara; transición de estado simple, mismo patrón que US-6.1.4)
- **Prioridad:** Alta — último paso del ciclo de la sesión; `US-6.2.8` y `US-6.2.9` dependen de ella

## Decisiones de Ejecución
- **BDD:** Sí — nueva funcionalidad con 8 escenarios Gherkin ya redactados en la spec.
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
- Contexto: docs/plans/inc6/US-6.2.7-context.md
- BDD feature: tests/features/inc6/US-6.2.7-finalizar-sesion-en-vivo.feature
- Plan: docs/plans/inc6/US-6.2.7-plan.md
- Reporte: docs/reports/inc6/US-6.2.7-report.md
- Quality report: quality/reports/inc6/US-6.2.7-quality.json

## Notas específicas del proyecto (no genéricas del skill)
- Rutas de plan/contexto/reporte/quality en subcarpeta `incN/`.
- Fase 7, en orden y sin paralelizar: 1) suite completa con cobertura, 2) `codeguard --analysis-type full`
  con `PATH="$PWD/.venv/bin:$PATH"`. `designreviewer` con `--config pyproject.toml`.
- En zsh, expandir listas de archivos con `${=VAR}` o `$(cat archivo)`.
- **CBO:** `finalizar_sesion` va en `ConduccionEnVivoController`; vigilar CBO al sumar el use case ahí
  (pre-push es el único gate que lo mide) — si roza 10/10, separar antes de pushear.
- **Decisión de spec (Víctor 2026-09-21):** finalizar sin restricción de última pregunta; solo INV-AEV-03.
- **Limpieza de tests previos:** reemplazar la siembra de `SesionEnVivoFinalizada` en tests de US-6.1.3/6.1.4
  por el endpoint real donde sea posible.
- **Regla de la sesión:** `tests/integration/` y BDD vacían la DB local compartida.
- Integración: incluir el mensaje `sesion_finalizada` completo a dos WebSockets conectados.
