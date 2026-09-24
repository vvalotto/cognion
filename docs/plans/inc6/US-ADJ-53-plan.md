# Plan de Implementación: US-ADJ-53 - Suite frontend con cobertura estable

**Estado:** BORRADOR — Fase 2 interrumpida el 2026-09-24 (apagado de la máquina). Retomar las mediciones.

## Mediciones parciales (2026-09-24, 8 núcleos, Vitest 4.1.10, sin `--testTimeout`)

| Configuración | Duración | Load average pico (1 min) | Resultado |
|---|---|---|---|
| Por defecto (todos los núcleos) | 180 s | 31 | 637/639 — 2 fallos en `NuevaPreguntaOpcionMultiple.test.tsx` |
| `--maxWorkers=4` (interrumpida) | > 336 s sin terminar | **275** | — |
| `--maxWorkers=2` | no corrió | — | — |

**Resultado inesperado:** con 4 workers la corrida fue más lenta y con mucha más carga que con todos los núcleos. Una
sola corrida cortada no alcanza para concluir. Hipótesis a verificar: en macOS el load average cuenta también hilos
esperando I/O, y `--coverage` (v8) escribe muchos archivos temporales en `coverage/.tmp`.

## Al retomar

1. Correr cada configuración **al menos 2 veces** (default, `maxWorkers=4`, `maxWorkers=2`, y `maxWorkers="50%"`).
2. Medir además de la carga: I/O de disco (`iostat -w 3`) y si el pico coincide con la escritura de cobertura.
3. Verificar que no queden procesos de Vitest vivos entre corridas (`pgrep -fl vitest`).
4. Elegir la configuración con datos y recién ahí cerrar el plan (Fase 2) y pedir aprobación.

## Script de medición

```zsh
#!/bin/zsh
# uso: medir.sh etiqueta [args extra de vitest]
etiqueta=$1; shift
cd /Users/victor/PycharmProjects/cognion/frontend
out=/private/tmp/claude-501/medicion-$etiqueta.log
( while true; do sysctl -n vm.loadavg | awk '{print $2}'; sleep 3; done ) > /private/tmp/claude-501/load-$etiqueta.txt &
muestreo=$!
inicio=$(date +%s)
npx vitest run --coverage --coverage.reportOnFailure --coverage.reporter=text-summary "$@" > $out 2>&1
fin=$(date +%s)
kill $muestreo
pico=$(sort -n /private/tmp/claude-501/load-$etiqueta.txt | tail -1)
tests=$(grep -E "^ +Tests " $out | sed 's/^ *//')
echo "$etiqueta | duracion=$((fin-inicio))s | load_pico=$pico | $tests"
```

## Alcance ya decidido (Fase 0)

- Script `npm run test:coverage` + configuración en `frontend/vite.config.ts`.
- Sección "Frontend (perfil `clean-architecture-bc`)" en `.claude/skills/implement-us/phases/phase-7-quality-gates.md`
  (gap: el comando de Fase 7 del frontend no estaba documentado en ningún lado).
