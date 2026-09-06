# Contexto de Ejecución — US-ADJ-16

## Fuentes
- **Fuente HU:** Documento local — `docs/specs/ajustes/US-ADJ-16.md`
- **Fuente Arquitectura:** `docs/rf/ARQ_v1.md` + `CLAUDE.md` — no aplica (tests frontend
  puros, sin cambio de arquitectura)

## Historia de Usuario
- **ID:** US-ADJ-16
- **Título:** Subir cobertura de branches del frontend (77.89% → 80%)
- **Tipo:** Tests (agregar casos, sin cambio de comportamiento)
- **Puntos:** 5
- **Prioridad:** Media — umbral configurado en `vitest.config.ts` como discrepancia silenciosa
  desde el cierre de `BL-004`

## Medición real al iniciar (la tabla de la spec es de antes de `US-ADJ-14`/`20` — se
remidió antes de tocar nada)

`npx vitest run --coverage --no-file-parallelism`: 41/41 archivos, 229/229 tests,
**Branches: 79.66% (517/649)** — ya no 77.89% (`US-ADJ-20` sumó cobertura incidental al tocar
los `useEffect`/submit de 21 páginas). Gap real: **+3 branches cubiertas** para cruzar el
umbral de 80% (520/649 = 80.12%).

Peor cobertura de branches por archivo (`coverage/coverage-final.json`, campo `b`):

| Archivo | Branches |
|---|---|
| `pages/actividad-evaluativa/EvaluacionSuspendida.tsx` | 2/4 (50%) |
| `pages/actividad-evaluativa/MateriasActividades.tsx` | 2/4 (50%, sin test file) |
| `pages/banco-preguntas/NuevaPreguntaTipo.tsx` | 4/8 (50%) |
| `pages/actividad-evaluativa/EditarTituloActividad.tsx` | 12/22 (54.55%) |
| `pages/actividad-evaluativa/Actividades.tsx` | 18/30 (60%, sin test file) |
| `pages/banco-preguntas/Materias.tsx` | 6/10 (60%) |
| `pages/actividad-evaluativa/CerrarActividad.tsx` | 5/8 (62.5%) |
| `pages/actividad-evaluativa/MisMaterias.tsx` | 5/8 (62.5%) |

## Decisiones de Ejecución
- **BDD:** No — agregar tests no es un cambio de comportamiento de dominio (tabla de
  clasificación de Fase 0).
- **skip_bdd:** true
- **Fases a ejecutar:** 0, 2, 3, 7, 8, 9 (se saltan 1, 4, 5 y 6 — la Fase 3 ya produce los
  tests nuevos, no hay Fase 4/5 separada para este tipo de US; Fase 7 corre `vitest --coverage`
  como gate real)
- **Alcance:** priorizar los archivos de menor % (tabla de arriba), empezando por
  `EvaluacionSuspendida.tsx` y `NuevaPreguntaTipo.tsx` (los que ya tienen test file, para no
  mezclar "agregar tests" con "crear test file desde cero" en la misma tarea) — suficiente para
  cerrar el gap real de +3 branches. Si no alcanza, seguir con el resto de la tabla.

## Perfil Activo
- **Perfil:** `clean-architecture-bc`
- **Patrón arquitectónico:** N/A — tests frontend, sin tocar backend
- **Umbrales de calidad (frontend):**
  - `npx vitest run --coverage --no-file-parallelism`: branches globales ≥ 80%
  - Ningún test existente se modifica de forma que deje de verificar lo que verificaba

## Rutas de Artefactos
- Contexto: `docs/plans/inc3-adj/US-ADJ-16-context.md`
- BDD feature: N/A (skip_bdd)
- Plan: `docs/plans/inc3-adj/US-ADJ-16-plan.md`
- Reporte: `docs/reports/inc3-adj/US-ADJ-16-report.md`
- Quality report: `quality/reports/inc3-adj/US-ADJ-16-quality.json`
