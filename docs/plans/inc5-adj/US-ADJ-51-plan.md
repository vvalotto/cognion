# Plan de Implementación: US-ADJ-51 - Docente ve la completitud de una actividad puntual

**Patrón:** clean-architecture-bc (esta US no toca capas de dominio — frontend puro)
**Producto:** analytics (frontend)

## Gap detectado en Fase 2 (antes de codear)

El endpoint `GET /analytics/actividades/{actividad_id}/completitud` (`US-ADJ-47`) devuelve, por
estudiante, solo `estudiante_id`/`nombre`/`estado` — **sin comisión**. La spec (`US-ADJ-51.md`
§Postcondición, `wireframes-analytics.md` §3.5) pide una columna Comisión cuando la actividad
mezcla más de una, pero también dice explícitamente: *"si está restringida a una sola, se puede
omitir en la implementación"* — deja margen de decisión de implementación, sin exigir backend
nuevo.

**Decisión (sin backend nuevo, mismo criterio que `US-ADJ-48`/`US-4.2.5`):** el frontend ya
conoce `materiaId` (vía `obtenerActividad`, `US-3.4.4`) y ya tiene los endpoints reutilizables
`listarComisionesPorMateria`/`listarEstudiantesDeComision`
(`frontend/src/lib/identidad-comisiones-api.ts`, consumidos por `DesempenoPorComision.tsx`/
`DesempenoPorAlumno.tsx`). `CompletitudActividad.tsx` arma un mapa `estudianteId → horario de
comisión` cruzando esas dos listas (todas las comisiones de la materia, no solo las de la
actividad — no hace falta filtrar, el mapa solo se usa para los estudiantes que ya vienen en el
`detalle` del backend) y decide mostrar la columna Comisión solo si el `detalle` contiene más de
un horario distinto. Sin cambios en `src/`.

## Componentes a Implementar

### 1. Cliente API
- [ ] `frontend/src/lib/analytics-api.ts`
  - Interfaces nuevas `CompletitudFilaResponse` (`estudianteId`, `nombre`, `estado`),
    `CompletitudResumenResponse` (`finalizadas`, `enCurso`, `suspendidas`, `sinIniciar`),
    `CompletitudPorActividadResponse` (`detalle`, `resumen`)
  - `obtenerCompletitudPorActividad(actividadId, signal?)` sobre
    `GET /analytics/actividades/{actividadId}/completitud`, mapeo snake_case→camelCase
    (`en_curso` → `enCurso`, `sin_iniciar` → `sinIniciar`)

### 2. Badge de estado
- [ ] `frontend/src/components/ui/badge.tsx`
  - 4 variantes nuevas: `completitud-finalizada` (verde), `completitud-en-curso` (azul),
    `completitud-suspendida` (ámbar), `completitud-sin-iniciar` (gris) — misma paleta que las
    variantes `estado-*`/`revision-*` ya existentes, sin componente propio nuevo

### 3. Pantalla nueva — completitud de una actividad
- [ ] `frontend/src/pages/analytics/CompletitudActividad.tsx`
  - Lee `actividadId` de `useParams`
  - `obtenerActividad(actividadId)` (`actividad-evaluativa-api.ts`, ya existente) → título +
    `materiaId` para breadcrumb y para resolver comisiones
  - `listarMaterias()` → nombre de la materia para el breadcrumb
  - `obtenerCompletitudPorActividad(actividadId)` → `detalle` + `resumen`
  - `listarComisionesPorMateria(materiaId)` + `listarEstudiantesDeComision` por cada comisión →
    mapa `estudianteId → horario`; columna Comisión visible solo si el `detalle` combinado con
    ese mapa tiene más de un horario distinto (gap de Fase 2, arriba)
  - Resumen `.completitud-summary` (o equivalente Tailwind): 4 números (Finalizadas, En curso,
    Suspendidas, Sin iniciar) — vienen directo de `resumen`, sin cálculo propio del frontend
    (invariante de la spec)
  - Tabla: Nombre, [Comisión condicional], Estado (`Badge` con las 4 variantes nuevas)
  - Breadcrumb "Actividades › {título de la actividad} › Completitud" con link a
    `/actividad-evaluativa/materias/{materiaId}/actividades` (mismo patrón que
    `ActividadDetalle.tsx`)
  - Sin selectores de materia/comisión — la actividad ya viene fijada por `actividadId`, a
    diferencia de `DesempenoPorComision.tsx`/`RankingPreguntasFalladas.tsx`

### 4. Entry point desde el detalle de actividad
- [ ] `frontend/src/pages/actividad-evaluativa/ActividadDetalle.tsx`
  - Botón "Ver completitud" (mismo estilo `variant="outline"` que "Extender plazo") que navega
    a `/actividad-evaluativa/actividades/{actividad.id}/completitud`

### 5. Integración de rutas
- [ ] `frontend/src/router.tsx`
  - `/actividad-evaluativa/actividades/:actividadId/completitud` →
    `RequireRole rol="docente"` → `CompletitudActividad` — vive en el namespace de Actividad
    Evaluativa (mismo criterio que la spec: se llega desde `ActividadDetalle.tsx`, no desde
    `/analytics/*`)
  - Sin entrada en `AppNav.tsx` (invariante de la spec: nunca es entrada directa del menú)

**Estado:** ✅ COMPLETADO — 5/5 tareas completadas
**Fecha completado:** 2026-09-15
**Tiempo real:** tracking de Fases 0, 2-5, 7-9. Detalle completo en
`docs/reports/inc5-adj/US-ADJ-51-report.md`.
