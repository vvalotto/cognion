# Reporte de Implementación: US-ADJ-53

## Resumen Ejecutivo

- **Historia de Usuario:** US-ADJ-53 — Corrida de la suite frontend con cobertura estable, sin flags manuales (Issue #432)
- **Puntos estimados:** 2
- **Tiempo real:** ver `.claude/tracking/US-ADJ-53-tracking.json` (la Fase 2 incluye la interrupción por apagado de la
  máquina, el tracker no tiene pausa)
- **Estado:** ✅ COMPLETADO
- **Fecha completado:** 2026-09-24
- **Origen:** Fase 7 de `US-6.3.7` — fallos aleatorios de la suite completa con cobertura.

---

## Cambios

- `frontend/vite.config.ts`: `testTimeout: 20000`, `coverage.reportOnFailure: true`.
- `frontend/package.json`: `npm run test:coverage` (`vitest run --coverage`).
- `.claude/skills/implement-us/phases/phase-7-quality-gates.md`: sección "Frontend (perfil `clean-architecture-bc`)"
  — **gap de Fase 0**: el comando de Fase 7 del frontend no estaba documentado en ningún lado, solo en los
  `quality.json` de cada US.

## Mediciones (Fase 2)

8 corridas, 4 configuraciones × 2 rondas intercaladas, reposo previo ~7-8 de load (8 núcleos). Detalle en
`docs/plans/inc6/US-ADJ-53-plan.md` y `quality/reports/inc6/US-ADJ-53-mediciones.txt`.

- **La cantidad de workers no causa la saturación.** Ronda B: todas las configuraciones con load promedio 10-15.
  Ronda A (primeros ~40 min tras encender la máquina): 230-245 de pico con 8 **y** con 4 workers, partiendo de 7 —
  carga ajena a Vitest (hipótesis sin confirmar: Spotlight o antivirus escaneando los temporales de cobertura).
- **Los timeouts de 5 s aparecen solo bajo esa carga ajena.**
- **Limitar workers solo alarga la corrida:** default 108 s, 4 workers 118 s, 50% 127 s, 2 workers 161 s (ronda B).
- `MateriasActividades` falló con carga baja (17-21): carrera del test, no saturación → `US-ADJ-54`.

**Decisión:** no limitar workers; `testTimeout` como margen; `reportOnFailure`.

## Verificación

| Corrida | Duración | Tests |
|---|---|---|
| `npm run test:coverage` #1 | 176 s | 639/639 |
| `npm run test:coverage` #2 | 138 s | 639/639 |
| `npm run test:coverage` #3 | 106 s | 639/639 |
| `npm run test` (CI) | 124 s | 639/639 |

Cobertura global 92,32% / 83,03% (umbral 80%). `tsc -b` y `oxlint` 0 errores. Evidencia:
`quality/reports/inc6/US-ADJ-53-verificacion.txt`.

## Criterios de Aceptación

- ✅ Un solo comando documentado · ✅ 3 corridas seguidas en verde · ✅ load por debajo de 116 con la máquina en reposo
  (con carga ajena puede superarlo: documentado) · ✅ el CI no cambia de comportamiento.

## Fuera de alcance / sugerencia

- Excluir `frontend/coverage/` de Spotlight y del antivirus para confirmar la hipótesis de la carga ajena
  (configuración de la máquina, no del repo).

## Lecciones Aprendidas

- Medir antes de configurar: la hipótesis inicial (demasiados workers) era falsa; la solución obvia (limitarlos)
  solo habría alargado la corrida.
- Una corrida de medición no alcanza: la misma configuración dio load 245 en una ronda y 20 en la otra. Medir el
  reposo previo y repetir intercalando configuraciones.
- La carga de una Mac recién encendida es alta durante un buen rato: no correr la Fase 7 sin mirar `uptime`.
