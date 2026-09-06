# Plan de Implementación: US-ADJ-13 - Documentar "Zone of Pain" de ArchitectAnalyst como falso positivo aceptado

**Patrón:** N/A — documentación + config de tooling, transversal (no toca `src/`)
**Producto:** cognion
**Estado:** ✅ COMPLETADO
**Fecha completado:** 2026-09-03

## Métricas de Tiempo

Tracking vía `.claude/tracking/tracker_cli.py` (`.claude/tracking/US-ADJ-13-tracking.json`).
Fases 1, 4, 5, 6 y 7 omitidas (sin código de producción ni comportamiento a testear/lintear —
decisión de Fase 0/2). Tiempo real acumulado hasta el cierre de Fase 8, sin comparación contra
estimación humana (`PRIN-001`).

## Lecciones Aprendidas

- 💡 Para una US de documentación + corrección de config inválida (sin código de producción),
  reducir el flujo a Fases 0, 2, 3, 8, 9 evita ceremonia sin valor (tests/quality gates que no
  tienen nada que medir) sin perder trazabilidad — mismo criterio ya aplicado en `US-ADJ-20`.
- ⚠️ Durante Fase 8 se detectó que el propio `CLAUDE.md` (actualizado en la sesión anterior,
  PR #218, sobre un hallazgo no relacionado a esta US) tenía un error de estado — dijo que
  `US-3.4.5`/`6`/`7` eran el próximo paso pendiente cuando ya estaban cerradas junto con
  `BL-004`/`v0.5.0`. Corregido en el mismo PR #218 antes de continuar. Lección: al citar el
  "próximo paso" o el estado de cierre de un incremento en `CLAUDE.md`, cruzar siempre contra
  `CHANGELOG.md`/tags — el texto libre de `CLAUDE.md` puede quedar desactualizado sin que nadie
  lo note hasta que se lo usa para decidir qué sigue.

## Componentes a Implementar

### 1. Config — `pyproject.toml`
- [x] `[tool.architectanalyst]`:
  - Eliminar `paths = ["src"]` (el CLI ya recibe el path por argumento posicional; el campo no
    existe en `ArchitectAnalystConfig`)
  - Renombrar `history_db = "quality/reports/architectanalyst/history.db"` →
    `db_path = "quality/reports/architectanalyst/history.db"` (mismo valor, campo real)
  - No tocar `[tool.architectanalyst.layers]` (fuera de alcance — `US-ADJ-19`)

### 2. Documentación — `CLAUDE.md`
- [x] Agregar nota en la sección "Quality gates" (bajo "Notas operativas críticas"): los 5
  críticos "Zone of Pain" de paquete raíz de BC (`identidad`, `settings`, `shared`,
  `banco_preguntas`, `actividad_evaluativa`) son un falso positivo aceptado permanentemente —
  causa raíz estructural (cada BC es hoja del grafo de dependencias por diseño, `Ca=0`), no un
  defecto de diseño real ni algo que `analysis_depth` resuelva (probado: sube de 5 a 15
  críticos). Referencia a `docs/specs/ajustes/US-ADJ-13.md` para el detalle de la investigación.

## Verificación (reemplaza Fases 1/4/5/6/7 — sin código de producción ni tests)

- [x] `architectanalyst src/ --config pyproject.toml` ya no emite
  `[tool.architectanalyst] clave desconocida ignorada: '...'` (confirmado: los 5 críticos
  "Zone of Pain" siguen apareciendo, como se espera — es el falso positivo aceptado, no algo
  a resolver)
- [x] `CLAUDE.md` contiene la explicación del falso positivo, localizable buscando "Zone of
  Pain" o "ArchitectAnalyst" (línea 644)

**Estado:** 4/4 tareas completadas
