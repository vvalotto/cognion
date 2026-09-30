# Reporte de Implementación: US-ADJ-51 - Docente ve la completitud de una actividad puntual

## Información General

| Campo | Valor |
|-------|-------|
| **Historia de Usuario** | US-ADJ-51 |
| **Título** | Docente ve la completitud de una actividad puntual |
| **Producto** | cognion (analytics, frontend) |
| **Prioridad** | Cuarta y última US de la Iteración 4 frontend del Incremento 5-ADJ — par backend→frontend de RF-23, cierra completa la Iteración 4 |
| **Puntos estimados** | 3 (sin asignación formal, mismo criterio que el resto de Analytics) |
| **Fecha inicio** | 2026-09-15 |
| **Fecha fin** | 2026-09-15 |
| **Tiempo real** | ~13 min de tracking (Fases 0, 2-5, 7-8) |
| **Estado** | ✅ COMPLETADO |

---

## Resumen Ejecutivo

Cierra el par backend→frontend de RF-23 (`US-ADJ-47`, backend, ya cerrado): pantalla de
completitud de una actividad puntual — resumen de 4 números (Finalizadas/En curso/
Suspendidas/Sin iniciar) más una tabla con el estado de cada estudiante del roster aplicable,
accesible únicamente desde el detalle de una actividad ya existente (`ActividadDetalle.tsx`,
`US-3.4.4`) vía el botón nuevo "Ver completitud" — nunca como entrada directa del menú de
Analytics, invariante explícita de la spec. Frontend puro, sin cambios de backend. Cierra
completa la Iteración 4 del Incremento 5-ADJ (`US-ADJ-44` a `51`): el Docente tiene los 4
informes de Analytics de RF-20 a RF-23 completos.

**Gap detectado en Fase 2 (antes de codear):** el endpoint de `US-ADJ-47`
(`GET /analytics/actividades/{id}/completitud`) no expone la comisión de cada estudiante en el
detalle — la spec dejaba margen explícito para omitir la columna Comisión cuando la actividad
está restringida a una sola. Resuelto sin backend nuevo: el frontend cruza
`listarComisionesPorMateria`/`listarEstudiantesDeComision` (ya usados por
`DesempenoPorComision.tsx`, `US-ADJ-48`) para armar un mapa estudiante→horario de comisión, y
muestra la columna solo si el resultado combina más de un horario distinto.

---

## Componentes Implementados

### Código Fuente (Backend)

Ninguno — US frontend puro, consume el endpoint ya expuesto por `US-ADJ-47`.

### Código Fuente (Frontend)

- ✅ `frontend/src/lib/analytics-api.ts` (modificado) — nuevas interfaces
  `CompletitudFilaResponse`, `CompletitudResumenResponse`, `CompletitudPorActividadResponse`,
  interfaces internas `*ApiResponse` correspondientes, mapper `mapearCompletitudPorActividad`,
  función `obtenerCompletitudPorActividad(actividadId, signal?)`
- ✅ `frontend/src/components/ui/badge.tsx` (modificado) — 4 variantes nuevas
  (`completitud-finalizada`, `completitud-en-curso`, `completitud-suspendida`,
  `completitud-sin-iniciar`), misma paleta que las variantes `estado-*`/`revision-*` ya
  existentes
- ✅ `frontend/src/pages/analytics/CompletitudActividad.tsx` (nuevo) — resumen `.completitud-summary`
  (4 números, directo de la respuesta del backend sin cálculo propio), tabla Nombre/[Comisión
  condicional]/Estado (`Badge`), breadcrumb "Actividades › {título} › Completitud", mapa
  estudiante→comisión resuelto en el frontend (gap de Fase 2, arriba)
- ✅ `frontend/src/pages/actividad-evaluativa/ActividadDetalle.tsx` (modificado) — botón "Ver
  completitud", visible siempre (a diferencia de "Extender plazo"/"Cerrar actividad ahora",
  que se ocultan si la actividad ya está cerrada manualmente — la completitud sigue siendo
  relevante después del cierre)
- ✅ `frontend/src/router.tsx` (modificado) — ruta nueva
  `/actividad-evaluativa/actividades/:actividadId/completitud`, `RequireRole rol="docente"` —
  vive en el namespace de Actividad Evaluativa (se llega desde `ActividadDetalle.tsx`, no
  desde `/analytics/*`), sin entrada en `AppNav.tsx`

**Total archivos:** 5 (0 backend, 5 frontend — 1 nuevo, 4 modificados)

---

### Tests

#### Tests Unitarios
- ✅ `frontend/src/pages/analytics/CompletitudActividad.test.tsx` (nuevo) — 4 tests: actividad
  restringida a una sola comisión (sin columna Comisión), actividad sin restricción con más de
  una comisión (con columna Comisión), resumen + badges por cada uno de los 4 estados, error de
  red al cargar la completitud
- ✅ `frontend/src/pages/actividad-evaluativa/ActividadDetalle.test.tsx` (modificado) — +2
  tests: el botón "Ver completitud" navega a la ruta nueva, visible incluso con la actividad ya
  cerrada manualmente

#### Tests de Integración
- ✅ `frontend/src/router.test.tsx` (modificado) — +2 tests: RBAC de la ruta de completitud
  (acceso denegado con sesión de estudiante, renderiza con sesión de docente)

#### Escenarios BDD

No aplica — frontend puro, mismo criterio que `US-ADJ-48`/`49`/`50`.

**Total tests nuevos/actualizados:** 8 nuevos · **Estado:** 494/494 frontend pasando (suite
completa con `--coverage`, sin flakes en esta corrida)

---

## Métricas de Calidad

| Métrica | Valor | Objetivo | Estado |
|---------|-------|----------|--------|
| **oxlint** | 0 errores (6 warnings preexistentes, no relacionados) | 0 errores | ✅ |
| **tsc -b** (`npm run build`) | 0 errores | 0 errores | ✅ |
| **Vitest** (suite completa) | 494/494 | Sin regresiones | ✅ |
| **Coverage `analytics-api.ts`** | 85.18% stmts, 50% branches, 88.23% funcs | — | ✅ |
| **Coverage `CompletitudActividad.tsx`** | 93.54% stmts, 80% branches, 86.36% funcs, 98.07% lines | — | ✅ |
| **Coverage `badge.tsx`** | 100% en las tres métricas | — | ✅ |
| **Coverage `router.tsx`** | 100% (línea de import) | — | ✅ |
| **Coverage `ActividadDetalle.tsx`** | 88.88% stmts, 77.77% branches — sin regresión, gaps preexistentes | — | ✅ |

Fuente: `quality/reports/inc5-adj/US-ADJ-51-quality.json`. No aplica CodeGuard/pylint/CC/MI —
sin cambios en `src/` (Python).

---

## Criterios de Aceptación

- [x] Actividad restringida a una comisión: resumen de 4 números + tabla sin columna Comisión
- [x] Actividad sin restricción (más de una comisión): tabla con columna Comisión, estudiantes
  de ambas comisiones
- [x] Estados variados (finalizada/en curso/suspendida/sin iniciar) renderizados con su propia
  variante de color de `Badge`
- [x] Acceso sin rol Docente: `RequireRole` bloquea la ruta

**Estado:** 4/4 cumplidos

---

## Arquitectura Implementada

### Patrón Aplicado

Frontend puro. A diferencia de `DesempenoPorComision.tsx`/`RankingPreguntasFalladas.tsx`, sin
selectores de Materia/Comisión — la actividad ya viene fijada por `actividadId` de la URL, el
patrón es más cercano a `ActividadDetalle.tsx` (un solo recurso identificado por id).

### Decisión de diseño: columna Comisión resuelta en el frontend

`CompletitudFilaResponse` del backend no trae comisión por estudiante. En vez de ampliar el
backend, `CompletitudActividad.tsx` cruza dos endpoints ya existentes
(`listarComisionesPorMateria` + `listarEstudiantesDeComision`, ambos consumidos ya por
`DesempenoPorComision.tsx`) para armar el mapa estudiante→horario, y decide mostrar la columna
solo si el `detalle` de la respuesta combina más de un horario distinto. La spec dejaba este
margen de implementación explícito. Documentado en `docs/plans/inc5-adj/US-ADJ-51-plan.md`
§Gap detectado en Fase 2.

---

## Cambios no Previstos

Ninguno respecto del plan aprobado.

---

## Testing Manual Realizado

Ninguno todavía en esta US — corresponde ahora el pase único de verificación manual en
navegador real con resiembra de base de datos (decisión operativa de Víctor, 2026-09-14): esta
US cierra completa la Iteración 4, así que la verificación manual queda como paso siguiente,
recorriendo los 4 informes de Analytics (`US-ADJ-48` a `51`) juntos. Ver
`feedback_uat_navegador_solo_cierre_iteracion` en la memoria del proyecto.

---

## Deuda Técnica

Ninguna introducida por esta US.

---

## Próximos Pasos

### Historias Relacionadas

Cierra completa la Iteración 4 del Incremento 5-ADJ (`US-ADJ-44` a `51`). Corresponde ahora:
1. Pase único de verificación manual en navegador real (con resiembra de base de datos) de los
   4 informes de Analytics.
2. Iteración 5 (revisión documental de cierre — `US-ADJ-52`).
3. Cierre de baseline (`BL-010`), siguiendo `WORKFLOW-DESARROLLO.md` §7.

---

## Tiempo Invertido

| Fase | Tiempo Real |
|------|-------------|
| Validación de Contexto | 34s |
| Plan | 116s |
| Implementación | 102s (5/5 tareas) |
| Tests Unitarios | 313s |
| Tests de Integración | 0s (cubiertos junto con Fase 4/router.test.tsx) |
| Quality Gates | 185s |
| Documentación | (en curso) |
| **TOTAL** | **~13 min de tracking efectivo (fases con registro)** |

---

## Lecciones Aprendidas

### Lo que Funcionó Bien

1. Detectar el gap de la columna Comisión en Fase 2 (antes de codear) evitó descubrirlo a
   mitad de la implementación — la spec ya anticipaba el margen de decisión, así que no hizo
   falta consultar a Víctor.
2. Reutilizar `listarComisionesPorMateria`/`listarEstudiantesDeComision` (ya consumidos por
   `DesempenoPorComision.tsx`) evitó tocar `src/` para un dato que el backend no necesitaba
   modelar como responsabilidad propia del endpoint de completitud.

### Recomendaciones para Próximas Historias

1. Al testear pantallas con varios `useEffect` encadenados que dependen de state asincrónico
   (como el mapa estudiante→comisión, poblado después de que la pantalla ya es visible), usar
   `findByText`/`waitFor` en vez de `getByText` para las aserciones que dependen del último
   efecto en resolver — un `getByText` inmediatamente después del primer `findBy` puede correr
   antes de que todos los efectos hayan asentado.
