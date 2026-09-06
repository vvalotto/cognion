# Plan de Implementación: US-ADJ-16 - Subir cobertura de branches del frontend (77.89% → 80%)

**Patrón:** N/A — tests frontend, sin cambio de comportamiento
**Producto:** cognion
**Estado:** ✅ COMPLETADO
**Fecha completado:** 2026-09-03

## Métricas de Tiempo

Tracking vía `.claude/tracking/tracker_cli.py` (`.claude/tracking/US-ADJ-16-tracking.json`).
Fases 1, 4, 5 y 6 omitidas (los tests nuevos se implementan directamente en Fase 3; Fase 7 usa
`vitest --coverage` como gate real). Tiempo real sin comparación contra estimación humana
(`PRIN-001`).

## Lecciones Aprendidas

- 💡 Medir el gap real antes de tocar nada evitó trabajo de más: la spec (basada en una medición
  de antes de `US-ADJ-14`/`20`) sugería 6 archivos a tocar para +2.11pp; el gap real medido al
  iniciar era solo +3 branches (`US-ADJ-20` ya había sumado cobertura incidental al tocar los
  `useEffect`/submit de 21 páginas para el `AbortController`).
- 💡 Inspeccionar `coverage/coverage-final.json` (campo `b`, por archivo) en vez de confiar en
  el resumen agregado de la consola permitió identificar la línea exacta sin cubrir
  (`onKeyDown` de dos `Card`, nunca ejercitadas por teclado) antes de escribir un solo test.

## Baseline real medido (no la tabla de la spec, desactualizada por `US-ADJ-14`/`20`)

`npx vitest run --coverage --no-file-parallelism`: 41/41 archivos, 229/229 tests,
**branches 79.66% (517/649)**. Gap real: **+3 branches cubiertas** para cruzar 80%
(520/649 = 80.12%).

## Componentes a Implementar

### 1. `pages/banco-preguntas/NuevaPreguntaTipo.test.tsx`
- [x] Test: presionar `Enter` sobre la Card "Opción múltiple" navega igual que el click
  (cubre branch de `onKeyDown` de la primera Card, línea 44, sin cubrir — `b: {"2":[0,0]}`)
- [x] Test: presionar `Enter` sobre la Card "Verdadero/Falso" navega igual que el click
  (cubre branch de `onKeyDown` de la segunda Card, línea 62, sin cubrir — `b: {"3":[0,0]}`)
- [x] Test: presionar una tecla que no sea `Enter` sobre una Card no navega (cubre el branch
  "false" de la condición `e.key === "Enter"`)

Verificado con `coverage/coverage-final.json` (campo `b`) antes de escribir: branches 2 y 3
(líneas 44 y 62) estaban en `[0,0]` — ningún test ejercitaba el teclado, solo `click`. 3 tests
nuevos alcanzaron para cerrar el gap completo: de 517/649 (79.66%) a 520/649 (80.12%) —
exactamente el gap medido (+3), sin necesidad de tocar más archivos.

## Verificación (reemplaza Fases 1/4/5/6 — tests nuevos son la Fase 3, Fase 7 corre el gate real)

- [x] `npx vitest run --coverage --no-file-parallelism`: branches globales 80.12% (520/649),
  sin el error "does not meet global threshold" — 41/41 archivos, 232/232 tests
- [x] Ningún test existente falla ni cambia su aserción original — solo se agregaron 3 casos

**Estado:** 3/3 tareas completadas
