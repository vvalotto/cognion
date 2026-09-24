# Plan de Implementación: US-ADJ-53 - Suite frontend con cobertura estable

**Estado:** APROBADO por Víctor 2026-09-24, tras completar las mediciones.

## Mediciones parciales (2026-09-24, 8 núcleos, Vitest 4.1.10, sin `--testTimeout`)

| Configuración | Duración | Load average pico (1 min) | Resultado |
|---|---|---|---|
| Por defecto (todos los núcleos) | 180 s | 31 | 637/639 — 2 fallos en `NuevaPreguntaOpcionMultiple.test.tsx` |
| `--maxWorkers=4` (interrumpida) | > 336 s sin terminar | **275** | — |
| `--maxWorkers=2` | no corrió | — | — |

**Resultado inesperado:** con 4 workers la corrida fue más lenta y con mucha más carga que con todos los núcleos. Una
sola corrida cortada no alcanza para concluir. Hipótesis a verificar: en macOS el load average cuenta también hilos
esperando I/O, y `--coverage` (v8) escribe muchos archivos temporales en `coverage/.tmp`.

## Mediciones completas (2026-09-24, tras reiniciar la máquina)

Reposo antes de cada corrida: load ~7-8, disco ~18 MB/s. Cada configuración 2 veces, intercaladas.

| Configuración | Ronda A: duración | Ronda A: load prom / pico | Ronda A: tests | Ronda B: duración | Ronda B: load prom / pico | Ronda B: tests |
|---|---|---|---|---|---|---|
| default (8 núcleos) | 240 s | 129 / 245 | 3 timeouts (5 s) | **108 s** | 13,5 / 20 | 639 ✓ |
| `maxWorkers=4` | 254 s | 131 / 234 | 639 ✓ | 118 s | 14 / 19 | 639 ✓ |
| `maxWorkers=50%` | 120 s | 17 / 27 | 1 fallo `MateriasActividades` | 127 s | 15 / 22 | 639 ✓ |
| `maxWorkers=2` | 281 s | 21 / 52 | 1 fallo `MateriasActividades` | 161 s | 10 / 16 | 639 ✓ |

**Conclusiones:**
1. La cantidad de workers **no** causa la saturación: en la ronda B todas corren con load 10-20; en la ronda A (primeros
   ~40 min tras encender la máquina) la carga subió a 230-245 con 8 **y** con 4 workers, partiendo de 7. Carga ajena a
   Vitest (hipótesis no confirmada: Spotlight o el antivirus escaneando los temporales de cobertura). Explica también
   los 116 de `US-6.3.7` y los 275 de la primera medición.
2. Los timeouts de 5 s solo aparecen bajo esa carga ajena.
3. El fallo de `MateriasActividades` aparece con carga baja (17-21): carrera real del test → `US-ADJ-54`.
4. La configuración por defecto es la más rápida (108 s); limitar workers solo alarga la corrida.

## Decisión (Fase 2)

- **No limitar workers** (default de Vitest).
- `test.testTimeout: 20000` en `frontend/vite.config.ts`: margen ante carga ajena. Aplica también al CI; solo cambia algo
  si un test se cuelga (falla a los 20 s en vez de 5 s).
- `test.coverage.reportOnFailure: true`: la tabla de cobertura sale aunque falle un test.
- Script `npm run test:coverage` (`vitest run --coverage`) en `frontend/package.json`.
- Sección "Frontend (perfil `clean-architecture-bc`)" en `.claude/skills/implement-us/phases/phase-7-quality-gates.md`
  con el comando y la nota: si `uptime` muestra carga alta sin tests corriendo, esperar a que baje antes de la Fase 7.

## Tareas

- [ ] `frontend/vite.config.ts` — `testTimeout`, `coverage.reportOnFailure`
- [ ] `frontend/package.json` — script `test:coverage`
- [ ] `phase-7-quality-gates.md` — sección Frontend
- [ ] Verificación: 3 corridas seguidas de `npm run test:coverage` (un fallo de `MateriasActividades` se registra, no
  bloquea: lo corrige `US-ADJ-54`); `npm run test` sigue pasando

## Procedimiento de medición (histórico)

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
