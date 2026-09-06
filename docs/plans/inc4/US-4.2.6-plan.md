# Plan de Implementación: US-4.2.6 - Docente ve "Desempeño por tema"

**Patrón:** Frontend puro (React + TypeScript), sin capas de Clean Architecture — no hay backend nuevo
**Producto:** cognion (frontend)
**Estado:** ✅ COMPLETADO
**Fecha completado:** 2026-09-06

## Métricas de Tiempo

Ver `.claude/tracking/US-4.2.6-tracking.json` — tiempo real de trabajo activo del agente
(fases 0, 2, 3, 4, 7, 8, 9; sin Fase 1/5/6 — BDD e integración backend no aplican, frontend
puro sin backend nuevo).

## Componentes a Implementar

### 1. Cliente API — extensión de `analytics-api.ts`
- [ ] `frontend/src/lib/analytics-api.ts`
  - Nuevo tipo `TasaErrorTemaResponse` (camelCase: `unidadTematica`, `tema`, `cantidadRespuestas`, `cantidadIncorrectas`, `tasaError`)
  - Nueva función `obtenerTasaErrorPorTema(materiaId, comisionId?, signal?)` sobre
    `GET /analytics/materias/{materia_id}/tasa-error-por-tema?comision_id=` (`US-4.2.4`, ya
    cerrado) — mapeo snake_case↔camelCase, mismo patrón que `obtenerDesempenoDeEstudiante`.
    `comisionId` opcional: si no viene, no se agrega el query param (agrega toda la materia).

### 2. Pantalla — `DesempenoPorTema.tsx`
- [ ] `frontend/src/pages/analytics/DesempenoPorTema.tsx`
  - Selectores en cascada: Materia (siempre, `listarMaterias()` de `banco-preguntas-api.ts`,
    ya usado en `DesempenoPorAlumno.tsx`) → Comisión (opcional, `listarComisionesPorMateria()`
    de `identidad-comisiones-api.ts`, con opción "Toda la materia" — value `""` — como default
    y primera opción del `<select>`)
  - Al elegir Materia: reconsulta `obtenerTasaErrorPorTema(materiaId)` sin `comisionId`
    (agregado de toda la materia) y puebla el selector de Comisión. Cambiar de Materia reinicia
    Comisión a `""` (invariante de la spec).
  - Al elegir una Comisión puntual: reconsulta `obtenerTasaErrorPorTema(materiaId, comisionId)`.
  - Elegir "Toda la materia" de nuevo (value `""`) desde una comisión ya elegida: reconsulta sin
    `comisionId`.
  - Listado: una fila por `(unidadTematica, tema)` — ya viene ordenado por `tasaError`
    descendente desde el backend (`ObtenerTasaErrorPorTemaUseCase`), sin reordenar en cliente.
  - Cada fila: rótulo pequeño de unidad + nombre del tema, barra de progreso coloreada
    (`width: {tasaError * 100}%`), % de tasa de error, pie con
    "{cantidadRespuestas} respuestas · {cantidadIncorrectas} incorrectas".
  - Severidad por umbral (función pura `severidad(tasaError: number)`, sin depender de ningún
    otro módulo): `>= 0.5` → `"alta"` (rojo, `text-red-600`/`bg-red-600`), `>= 0.2` → `"media"`
    (ámbar, `text-amber-600`/`bg-amber-600`), si no → `"baja"` (verde,
    `text-emerald-700`/`bg-emerald-700` — mismo tono que `DesempenoResumenDetalle.tsx`).
  - Estado vacío: si la lista resuelta viene vacía (materia o comisión sin ninguna `Evaluacion`
    finalizada) → mensaje de estado vacío, sin listado (mismo texto/estilo que
    `DesempenoPorAlumno.tsx`/`DesempenoResumenDetalle.tsx`).
  - Antes de elegir Materia: mensaje "Elegí una materia para ver la tasa de error por tema."
  - Manejo de error de red: mismo patrón `role="alert"` que `DesempenoPorAlumno.tsx`.
  - `AbortController` en cada `useEffect` de fetch (`US-ADJ-20`).

### 3. Ruta — `router.tsx`
- [ ] `frontend/src/router.tsx`
  - Import de `DesempenoPorTema`
  - Nueva ruta `/analytics/desempeno-por-tema` protegida con `RequireRole rol="docente"` (mismo
    bloque que `/analytics/desempeno-por-alumno`)

## Integración
- [ ] Ninguna integración de backend — `US-4.2.4` ya expone el endpoint consumido.
- [ ] No hay componente compartido que extraer (a diferencia de `US-4.2.5`, que reutilizó
  `DesempenoResumenDetalle.tsx`): esta pantalla tiene forma propia (`.tema-row`), sin resumen
  acumulado ni detalle por evaluación.

**Estado:** 3/3 tareas completadas
