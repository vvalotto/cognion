# Reporte de Implementación: US-ADJ-20

## Resumen Ejecutivo

- **Historia de Usuario:** US-ADJ-20 - `AbortController` en los fetch de `useEffect`/submit del frontend
- **Puntos estimados:** 5
- **Estado:** ✅ COMPLETADO
- **Fecha completado:** 2026-09-02
- **Origen:** investigación durante el triage de PRs de Dependabot — un `unhandled rejection`
  intermitente en CI (`ECONNREFUSED` / `TypeError: Cannot read properties of undefined (reading
  'status')`) resultó ser una condición de carrera real y pre-existente en `develop`, no algo
  introducido por ningún bump de dependencia.

---

## Causa raíz

21 componentes de `frontend/src/pages/` usaban el patrón `let cancelado = false` en sus
`useEffect` con fetch: evita el `setState` posterior al desmontaje, pero no cancela el `fetch`
en sí — la promesa de red sigue en vuelo, sin ningún `.catch`. En tests, cada archivo reemplaza
`global.fetch` con un `vi.fn()` nuevo por `beforeEach`; si la promesa de un componente ya
desmontado se resuelve después de que el siguiente test ya instaló su propio mock vacío,
`fetch()` devuelve `undefined` sincrónicamente y el código explota en `apiFetch`
(`response.status` sobre `undefined`), o cae al `fetch` real de Node en CI (`ECONNREFUSED`).
Confirmado como condición de timing, no determinística, reproducida en corridas de CI de PRs de
Dependabot sin relación entre sí (`#126` bump de vitest, `#129` bump de `@tailwindcss/vite`) y
también en `develop` sin ningún cambio de código (comparado con `git stash` del branch limpio
bajo la misma carga de máquina).

---

## Componentes Implementados

### Capa de API tipada — `signal?: AbortSignal`
- ✅ `frontend/src/lib/actividad-evaluativa-api.ts` (13 funciones)
- ✅ `frontend/src/lib/banco-preguntas-api.ts` (8 funciones)
- ✅ `frontend/src/lib/cuentas-api.ts` (5 funciones)
- ✅ `frontend/src/lib/identidad-estudiante-api.ts` (1 función)

`api-client.ts` no se tocó — `ApiFetchOptions extends Omit<RequestInit, "body">` ya propagaba
`signal` al `fetch` interno sin cambios.

### 21 componentes con `useEffect` + fetch — `cancelado` → `AbortController`
`ActividadDetalle`, `Actividades`, `Banco`, `CerrarActividad`, `CuentaDetalle`, `Cuentas`,
`EditarPregunta`, `EditarTituloActividad`, `EliminarPregunta`, `EvaluacionSuspendida`,
`ExtenderPlazo`, `Materias`, `MateriasActividades`, `MisActividades`, `MisMaterias`,
`NuevaActividad`, `NuevaPreguntaOpcionMultiple`, `NuevaPreguntaTipo`,
`NuevaPreguntaVerdaderoFalso`, `RendirEvaluacion`, `ResetearPassword`, `RevisionEvaluacion`.
Cada efecto: `AbortController` local, `.catch(() => {})` para no dejar la promesa sin manejar
sea cual sea el motivo del rechazo, cleanup con `controller.abort()`.

### 12 formularios con `handleSubmit` async
`AltaDocente`, `CambiarPassword`, `EditarPregunta`, `EditarTituloActividad`, `ExtenderPlazo`,
`Login`, `NuevaActividad`, `NuevaMateria`, `NuevaPreguntaOpcionMultiple`,
`NuevaPreguntaVerdaderoFalso`, `Registro`, `ResetearPassword`. `AbortController` de ciclo de
vida del componente (`useRef` con init perezoso + `useEffect` de cleanup en el montaje), pasado
al submit; el `catch` de cada `handleSubmit` chequea `controladorSubmitRef.current?.signal
.aborted` antes de decidir si re-lanza el error — necesario porque el mock de `fetch` en los
tests (`vi.fn()`) no interpreta `AbortSignal`, así que `abort()` no cancela la promesa mockeada
en sí; el chequeo explícito de la bandera cubre ese caso igual, sin depender de que el mock
rechace con `AbortError`. En producción, con `fetch` real, el abort además cancela la petición.

31 archivos modificados en total (4 de API + 27 de páginas).

---

## Métricas de Calidad

| Métrica | Valor | Umbral | Estado |
|---------|-------|--------|--------|
| oxlint | 0 errores (4 warnings preexistentes) | 0 errores | ✅ |
| `tsc --noEmit` | 0 errores | 0 errores | ✅ |
| Vitest | 229/229 passed, 8+ corridas seguidas sin `unhandled rejection` | 100% pasan | ✅ |
| Coverage global frontend | 90.34% stmts, 92.59% lines, 79.66% branches | ≥80% stmts/lines | ⚠️ branches |
| pytest backend | 739/739 passed | 100% pasan | ✅ (sin cambios esperados) |

Fuente: `quality/reports/inc3-adj/US-ADJ-20-quality.json`. Branches (79.66%) queda debajo del umbral de
80% — gap pre-existente de `US-ADJ-16` (77.89% antes de esta US, ya en la lista de candidatas
del Incremento 3-ADJ), no en el alcance de `US-ADJ-20`.

**Estado General:** ✅ APROBADO

---

## Tests

Sin tests nuevos — según el plan aprobado (`docs/plans/inc3-adj/US-ADJ-20-plan.md`), la evidencia de
cierre es la suite Vitest existente (229 tests, 41 archivos) corriendo estable y repetidamente
sin `unhandled rejection`, verificado en 8+ corridas consecutivas. Bajo carga alta de máquina
(procesos en paralelo) reaparecen timeouts de 5000ms en tests de submit con muchos campos —
confirmado como flakiness pre-existente en `develop` sin relación con este cambio (mismo
síntoma con `git stash` del branch limpio, bajo la misma carga).

Sin BDD — clasificada como refactorización sin cambio de comportamiento observable (Fase 0).

---

## Archivos Creados/Modificados

### Código de producción (31 archivos, frontend)
- `frontend/src/lib/actividad-evaluativa-api.ts`, `banco-preguntas-api.ts`, `cuentas-api.ts`,
  `identidad-estudiante-api.ts`
- `frontend/src/pages/{ActividadDetalle,Actividades,AltaDocente,Banco,CambiarPassword,
  CerrarActividad,CuentaDetalle,Cuentas,EditarPregunta,EditarTituloActividad,EliminarPregunta,
  EvaluacionSuspendida,ExtenderPlazo,Login,Materias,MateriasActividades,MisActividades,
  MisMaterias,NuevaActividad,NuevaMateria,NuevaPreguntaOpcionMultiple,NuevaPreguntaTipo,
  NuevaPreguntaVerdaderoFalso,Registro,RendirEvaluacion,ResetearPassword,
  RevisionEvaluacion}.tsx`

### Documentación
- `docs/specs/ajustes/US-ADJ-20.md`
- `docs/plans/inc3-adj/inc3-adj-candidatas.md` (fila nueva + criterio de cierre actualizado)
- `docs/plans/inc3-adj/US-ADJ-20-context.md`
- `docs/plans/inc3-adj/US-ADJ-20-plan.md`
- `docs/reports/inc3-adj/US-ADJ-20-report.md` (este archivo)
- `quality/reports/inc3-adj/US-ADJ-20-quality.json`

---

## Criterios de Aceptación

- [x] Ningún componente desmontado deja un fetch de `useEffect` pendiente sin manejar
- [x] Ningún submit en vuelo rompe si el componente se desmonta (chequeo de `signal.aborted`)
- [x] La suite de tests deja de mostrar el `unhandled rejection`/`ECONNREFUSED` de forma
  reproducible (8+ corridas limpias consecutivas; residual de timing bajo carga de máquina,
  pre-existente, documentado como tal)

---

## Notas para el Cierre del Incremento 3-ADJ

`US-ADJ-20` se agregó durante esta sesión, fuera de la lista original de 7 candidatas
(`US-ADJ-13` a `19`) de `docs/plans/inc3-adj/inc3-adj-candidatas.md`. El criterio de cierre del
incremento pasa de "7 US-ADJ implementadas" a "8".
