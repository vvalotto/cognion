# Contexto de Ejecución — US-6.2.9

## Fuentes
- **Fuente HU:** Documento local — `docs/specs/inc6/US-6.2.9.md`, GitHub Issue [#400](https://github.com/vvalotto/cognion/issues/400)
- **Fuente Arquitectura:** `CLAUDE.md` (§Arquitectura interna — reglas no negociables) + `docs/design/domain/BC-actividad-evaluativa-modelo.md` §12–§17

## Historia de Usuario
- **ID:** US-6.2.9
- **Título:** Verificación de la sesión en vivo completa y del RNF de rendimiento
- **Tipo:** Verificación (UAT backend — sin código de producción)
- **Puntos:** 3 (la spec no lo declara; transición de estado simple, mismo patrón que US-6.1.4)
- **Prioridad:** Alta — cierra la Iteración 2 y el hito del Incremento 6 (RNF de rendimiento duro)

## Decisiones de Ejecución
- **BDD:** No — verificación: los 5 escenarios de la spec se implementan como tests de integración/medición (`test_sesion_en_vivo_completa.py`, `medir_rendimiento_cierre.py`), sin `.feature` propio.
- **skip_bdd:** true
- **Fases a ejecutar:** 0, 2, 3, 4, 5, 7, 8, 9 (sin 1 y 6 — sin BDD; sin código de producción a testear unitariamente)

## Perfil Activo
- **Perfil:** clean-architecture-bc
- **Patrón arquitectónico:** clean-architecture (entities → use_cases → interface_adapters → frameworks, BC-first)
- **Umbrales de calidad:**
  - pylint ≥ 8.0 (el proyecto viene sosteniendo ≥9.0)
  - CC ≤ 10
  - MI ≥ 20
  - cobertura ≥ 95.0%

## Rutas de Artefactos
- Contexto: docs/plans/inc6/US-6.2.9-context.md
- Plan: docs/plans/inc6/US-6.2.9-plan.md
- Reporte: docs/reports/inc6/US-6.2.9-report.md
- Quality report: quality/reports/inc6/US-6.2.9-quality.json

## Notas específicas del proyecto (no genéricas del skill)
- Rutas de plan/contexto/reporte/quality en subcarpeta `incN/`.
- **Sin código de producción**: si la medición da p95 > 100 ms es un hallazgo bloqueante de la iteración
  (US-ADJ u decisión con Víctor); no se optimiza dentro de esta US.
- **`git add` solo de rutas concretas**: nunca `git add tests` — arrastra `tests/uat/datos-reales/`.
- `tests/uat/inc6/` y `quality/reports/uat/inc6/` son nuevos; convención en `docs/plans/PROCEDIMIENTO-UAT.md`.
- Fase 7: suite completa con cobertura (vacía la DB local) y `codeguard --analysis-type full` sobre los
  `.py` de `src/` modificados (ninguno esperado). `RF-08/09/10` → Implementado solo tras validar Víctor.
- Editar planes/specs con Python; `tracker_cli.py` invocado directo.
