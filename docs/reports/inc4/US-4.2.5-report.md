# Reporte de Implementación: US-4.2.5

## Resumen Ejecutivo

- **Historia de Usuario:** US-4.2.5 - Docente ve "Desempeño por alumno"
- **Puntos estimados:** 3
- **Tiempo real:** ~17 min de trabajo activo del agente (fases 0-9, ver
  `.claude/tracking/US-4.2.5-tracking.json`)
- **Estado:** ✅ COMPLETADO
- **Fecha completado:** 2026-09-06

---

## Alcance

Frontend puro, sin cambios de backend — consume `GET /analytics/materias/{materia_id}/estudiantes/{estudiante_id}/desempeno`
(`US-4.2.1`), `GET /materias/{materia_id}/comisiones` y `GET /comisiones/{comision_id}/estudiantes`
(`US-4.2.2`), tal cual quedaron. El wireframe (`wireframes-analytics.md` §4, hot spot 2) exige
que esta pantalla reutilice el mismo componente visual que "Mi desempeño" (`US-4.1.3`) — se
extrajo `DesempenoResumenDetalle.tsx` de `MiDesempeno.tsx` sin cambiar su comportamiento
observable, y ambas pantallas lo consumen ahora. No mueve ninguna fila de la matriz de
trazabilidad por sí sola — RF-16 pasa a Implementado recién cuando cierre la Iteración 2
completa (junto con `US-4.2.6`).

---

## Componentes Implementados

### Frontend
- ✅ **`analytics-api.ts`** (modificado, `frontend/src/lib/analytics-api.ts`) — agrega
  `obtenerDesempenoDeEstudiante(materiaId, estudianteId, signal?)`, mismo mapeo
  snake_case→camelCase que `obtenerMiDesempeno` (factorizado en `mapearDesempenoEstudiante`)
- ✅ **`identidad-comisiones-api.ts`** (nuevo, `frontend/src/lib/identidad-comisiones-api.ts`) —
  `listarComisionesPorMateria(materiaId)`, `listarEstudiantesDeComision(comisionId)`, tipos
  `ComisionResumenResponse`/`EstudianteResumenResponse` (sin mapeo, la API ya devuelve camelCase
  plano)
- ✅ **`DesempenoResumenDetalle.tsx`** (nuevo, `frontend/src/pages/analytics/`) — componente
  visual único de resumen acumulado + detalle por evaluación, extraído de `MiDesempeno.tsx`;
  exporta también `armarFilas` y el tipo `FilaDesempeno`
- ✅ **`MiDesempeno.tsx`** (modificado) — reemplaza el bloque de JSX extraído por
  `<DesempenoResumenDetalle />`, sin cambio de comportamiento observable
- ✅ **`DesempenoPorAlumno.tsx`** (nueva, `frontend/src/pages/analytics/`) — pantalla
  `#doc-desempeno-alumno`: selectores en cascada Materia (`listarMaterias()`, docente) →
  Comisión → Estudiante, placeholder antes de elegir Estudiante, reutiliza
  `DesempenoResumenDetalle`/`armarFilas`, resuelve títulos de actividad con `listarActividades()`
  (docente)
- ✅ **`router.tsx`** — nueva ruta `/analytics/desempeno-por-alumno`, protegida con
  `<RequireRole rol="docente">`

---

## Métricas de Calidad

| Métrica | Valor | Umbral | Estado |
|---------|-------|--------|--------|
| oxlint | 0 errores, 5 warnings (4 preexistentes + 1 nuevo no bloqueante) | 0 errores | ✅ |
| `tsc --noEmit` | 0 errores | 0 errores | ✅ |
| Coverage `DesempenoPorAlumno.tsx` (statements/branches/functions/lines) | 95.45% / 73.68% / 82.6% / 96.61% | ≥ 80% (statements) | ✅ |
| Coverage `DesempenoResumenDetalle.tsx` (statements/branches/functions/lines) | 100% / 83.33% / 100% / 100% | ≥ 80% (statements) | ✅ |
| Coverage `MiDesempeno.tsx` tras el refactor | 100% / 89.47% / 91.66% / 100% (sin cambio vs. antes de esta US) | ≥ 80% (statements) | ✅ |
| Coverage `analytics-api.ts` / `identidad-comisiones-api.ts` | 100% / 100% / 100% / 100% (ambos) | ≥ 80% (statements) | ✅ |

Fuente: `quality/reports/inc4/US-4.2.5-quality.json`.

**Estado General:** ✅ APROBADO

---

## Tests Implementados

### Frontend

**Unitarios (8 tests nuevos, Vitest)**
- `analytics-api.test.ts` (+2 tests): `obtenerDesempenoDeEstudiante` mapea a camelCase, lista
  vacía de evaluaciones
- `identidad-comisiones-api.test.ts` (nuevo, 4 tests): `listarComisionesPorMateria` y
  `listarEstudiantesDeComision`, caso con datos y caso vacío de cada uno

**Componente (4 tests nuevos, `DesempenoPorAlumno.test.tsx`)**
- Estado inicial: placeholder sin resumen ni lista
- Recorrido completo en cascada: Materia → Comisión → Estudiante muestra resumen y detalle
- Estudiante sin evaluaciones finalizadas: estado vacío
- Cambiar de Materia reinicia Comisión, Estudiante y el resultado mostrado

`MiDesempeno.test.tsx` (6 tests preexistentes) siguió pasando sin modificaciones tras el
refactor — confirma que la extracción de `DesempenoResumenDetalle.tsx` no cambió comportamiento.

**Todos los tests de esta US pasando:** ✅ 18/18 (4 archivos)

**Nota sobre la suite completa:** al correr `vitest run` con la suite completa (252 tests), se
observaron 1-2 fallas intermitentes en archivos no tocados por esta US
(`NuevaPreguntaOpcionMultiple.test.tsx`, `ResetearPassword.test.tsx`, `NuevaActividad.test.tsx`,
distinto archivo en cada corrida) — reproducido en 3 corridas de la suite completa, y las 3
pasan siempre en ejecución aislada. Confirmado con `git stash` que la misma flakiness aparece
también en `develop` sin los cambios de esta US. Flakiness preexistente del entorno de test
(probable contención de recursos al correr en paralelo), no una regresión de US-4.2.5 — queda
fuera del alcance de esta US corregirla.

---

## Archivos Creados/Modificados

### Código de producción — frontend
- `frontend/src/lib/analytics-api.ts` (modificado)
- `frontend/src/lib/identidad-comisiones-api.ts` (nuevo)
- `frontend/src/pages/analytics/DesempenoResumenDetalle.tsx` (nuevo)
- `frontend/src/pages/analytics/MiDesempeno.tsx` (modificado — refactor sin cambio de comportamiento)
- `frontend/src/pages/analytics/DesempenoPorAlumno.tsx` (nuevo)
- `frontend/src/router.tsx` (modificado — import + ruta nueva)

### Tests
- `frontend/src/lib/analytics-api.test.ts` (modificado)
- `frontend/src/lib/identidad-comisiones-api.test.ts` (nuevo)
- `frontend/src/pages/analytics/DesempenoPorAlumno.test.tsx` (nuevo)

### Documentación
- `docs/specs/inc4/US-4.2.5.md` (ya existente, sin cambios de alcance)
- `docs/plans/inc4/US-4.2.5-context.md`
- `docs/plans/inc4/US-4.2.5-plan.md`
- `docs/plans/inc4/inc4-candidatas.md` (marcado el cierre de esta US)
- `docs/reports/inc4/US-4.2.5-report.md` (este archivo)
- `quality/reports/inc4/US-4.2.5-quality.json`

---

## Criterios de Aceptación

- [x] Recorrido completo en cascada: elegir Materia → Comisión → Estudiante con evaluaciones
      finalizadas muestra el resumen acumulado y el detalle por evaluación
- [x] Estudiante sin evaluaciones finalizadas: mensaje de estado vacío, sin resumen ni lista
- [x] Cambiar el selector de Materia reinicia Comisión y Estudiante, y el resumen desaparece
- [x] Acceso sin rol Docente: redirigido por `RequireRole`, no ve la pantalla (verificado por
      el patrón ya cubierto en `RequireRole.test.tsx` — la pantalla no implementa RBAC propio)

**Todos los criterios cumplidos:** ✅

---

## Próximos Pasos

- [ ] `US-4.2.6` (Docente ve "Desempeño por tema") — cierra completa la Iteración 2 del
      Incremento 4, `docs/plans/inc4/inc4-candidatas.md`
- [ ] UAT de cierre de la Iteración 2 del Incremento 4 (backend + frontend juntos), tras
      cerrar `US-4.2.6`

---

## Lecciones Aprendidas

- ⚠️ Encadenar `useEffect`s que se resetean unos a otros por dependencia de estado (materia →
  comisión → estudiante) introduce una carrera real: al cambiar la Materia, el efecto de
  "desempeño" (dependiente de `materiaId` + `estudianteId`) puede dispararse una vez con el
  `estudianteId` viejo antes de que el efecto de reseteo lo limpie, en el render intermedio.
  Se corrigió moviendo los resets a los manejadores `onChange` (mismo batch de React que el
  cambio de selección) en vez de depender de que otro efecto los limpie — los tests de
  cascada de `DesempenoPorAlumno.test.tsx` expusieron el bug antes de llegar a Fase 7.
- 💡 Extraer el componente visual compartido (`DesempenoResumenDetalle.tsx`) fue más simple
  parametrizando `filas`/`mensajeVacio` como props ya resueltas por el caller, en vez de pasar
  `titulosPorActividad` y recalcular `armarFilas` adentro — cada pantalla arma sus filas con
  su propia fuente de títulos de actividad (estudiante vs. docente) sin que el componente
  compartido necesite conocer esa diferencia.
- 💡 La flakiness de la suite completa de Vitest (archivos no tocados fallando de forma no
  determinística según la corrida) se descartó como regresión propia comparando contra
  `develop` limpio (`git stash`) antes de invertir tiempo en diagnosticarla — vale la pena
  dejarlo como patrón de verificación para US frontend futuras.

---

**Reporte generado automáticamente por Claude Code**
**Fecha:** 2026-09-06
