# Plan de Implementación: US-4.2.5 - Docente ve "Desempeño por alumno"

**Estado:** ✅ COMPLETADO — 2026-09-06

**Patrón:** Frontend puro (React + TypeScript), sin cambios de backend — reutiliza `US-4.2.1`
(`GET /analytics/materias/{materia_id}/estudiantes/{estudiante_id}/desempeno`) y `US-4.2.2`
(`GET /materias/{materia_id}/comisiones`, `GET /comisiones/{comision_id}/estudiantes`).
**Producto:** cognion (frontend)

## Componentes a Implementar

### 1. Cliente API

- [x] `frontend/src/lib/analytics-api.ts`
  - Agrega `obtenerDesempenoDeEstudiante(materiaId, estudianteId, signal?)` — mismo mapeo
    snake_case→camelCase que `obtenerMiDesempeno`, mismo tipo de retorno
    (`DesempenoEstudianteResponse`, sin tipo nuevo).
- [x] `frontend/src/lib/identidad-comisiones-api.ts` (nuevo archivo)
  - `ComisionResumenResponse { id, horario }`, `EstudianteResumenResponse { id, nombre }`
  - `listarComisionesPorMateria(materiaId, signal?)` → `GET /materias/{materiaId}/comisiones`
  - `listarEstudiantesDeComision(comisionId, signal?)` → `GET /comisiones/{comisionId}/estudiantes`
  - Archivo separado de `identidad-estudiante-api.ts` (ese es estudiante-facing) y de
    `identidad-api.ts` (no existe todavía como archivo único) — nombre explícito por lo que
    expone, mismo criterio de nombrar por función que `actividad-evaluativa-api.ts` /
    `banco-preguntas-api.ts`.

### 2. Extracción del componente visual compartido (invariante: mismo componente que "Mi desempeño")

- [x] `frontend/src/pages/analytics/DesempenoResumenDetalle.tsx` (nuevo archivo)
  - Extrae de `MiDesempeno.tsx` sin cambiar comportamiento: `formatearFecha`, `FilaDesempeno`
    (exportada), `armarFilas` (exportada) y el bloque JSX de resumen acumulado (4 cards) +
    detalle por evaluación. El estado vacío quedó dentro del propio componente (early return),
    parametrizado por `mensajeVacio` — más simple que pasar `filas` ya filtradas desde afuera.
  - Props reales: `{ desempeno: DesempenoEstudianteResponse, filas: FilaDesempeno[], mensajeVacio: string }`
    (el caller arma `filas` con `armarFilas`, mismo criterio en ambas pantallas).
- [x] `frontend/src/pages/analytics/MiDesempeno.tsx` (modificado)
  - Reemplaza el bloque extraído por `<DesempenoResumenDetalle desempeno={...} filas={...} mensajeVacio={...} />`.
  - Sin cambio de comportamiento observable — `MiDesempeno.test.tsx` no requirió ajustes.

### 3. Pantalla nueva

- [x] `frontend/src/pages/analytics/DesempenoPorAlumno.tsx` (nuevo archivo)
  - Selector Materia: `listarMaterias()` de `banco-preguntas-api.ts` (`US-2.1.9`, ya usado por
    el Docente en otras pantallas) — no `listarMisMaterias()` (ese es estudiante).
  - Selector Comisión: poblado por `listarComisionesPorMateria(materiaId)` al elegir Materia;
    se limpia junto con Estudiante si cambia la Materia.
  - Selector Estudiante: poblado por `listarEstudiantesDeComision(comisionId)` al elegir
    Comisión; se limpia si cambia la Comisión (o la Materia).
  - Sin Estudiante elegido → placeholder "Elegí un estudiante para ver su desempeño", sin
    resumen ni lista (wireframe §3.0).
  - Al elegir Estudiante → `Promise.all([obtenerDesempenoDeEstudiante(materiaId, estudianteId), listarActividades(materiaId)])`
    (`listarActividades` de `actividad-evaluativa-api.ts`, ya usado por el Docente — reemplaza
    a `listarActividadesVisibles` que es estudiante-facing) para resolver título de actividad
    por evaluación, igual que `MiDesempeno.tsx`.
  - Reutiliza `armarFilas` (de `DesempenoResumenDetalle.tsx`) y renderiza
    `<DesempenoResumenDetalle />` con el resultado.
  - `AbortController` creado dentro de cada `useEffect` (no en el render — patrón fijado por
    `US-ADJ-20`/gap detectado en la UAT de Iteración 1).
  - Breadcrumb "Analytics › Desempeño por alumno".

### 4. Integración

- [x] `frontend/src/router.tsx`
  - Import de `DesempenoPorAlumno`.
  - Ruta nueva `/analytics/desempeno-por-alumno`, envuelta en `RequireRole rol="docente"`
    (mismo patrón que el resto de rutas docente).

**Estado:** 5/5 tareas completadas — `tsc --noEmit` 0 errores tras la implementación.
Sin código obsoleto detectado.

---

## Fuera de alcance (confirmado por la spec)

- Sin backend nuevo — `US-4.2.1`/`US-4.2.2` ya cierran los 3 endpoints que esta US consume.
- Sin paginación del selector de Estudiante — wireframe §4 lo deja pendiente de definir "si
  hace falta" a esta escala (30-60 alumnos); un `<select>` simple alcanza, mismo criterio que
  el resto de selectores de materia/comisión ya implementados.
- Sin navegación desde la fila de evaluación a la revisión pregunta por pregunta (wireframe §4,
  hot spot 3 — explícitamente fuera de alcance de RF-16).
