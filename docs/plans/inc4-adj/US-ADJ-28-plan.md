# Plan de Implementación: US-ADJ-28 - Home del Docente

**Patrón:** Frontend puro (sin capas de dominio)
**Producto:** cognion
**Estado:** ✅ COMPLETADO — 2/2 tareas, quality gates APROBADO
(`quality/reports/inc4-adj/US-ADJ-28-quality.json`)

## Componentes a Implementar

### 1. `HomeDocente.tsx` (pantalla nueva)

- [x] `frontend/src/pages/HomeDocente.tsx`
  - Sin breadcrumb (es la raíz)
  - `<h1>Hola, Docente</h1>` (saludo genérico — decisión de Fase 0, sin `GET /usuarios/me`)
  - Grid de 4 `Card` (mismo componente ya usado en `Actividades.tsx`/`MateriasActividades.tsx`),
    cada una con `role="button"` + `onClick`/`onKeyDown` (mismo patrón de accesibilidad ya
    usado en esas pantallas):
    - Banco de Preguntas → `/materias`
    - Actividades → `/actividad-evaluativa/materias`
    - Desempeño por alumno → `/analytics/desempeno-por-alumno`
    - Desempeño por tema → `/analytics/desempeno-por-tema`

### 2. Ruta índice condicional por rol

- [x] `frontend/src/pages/Inicio.tsx` (nuevo) — componente que lee `getSession()?.rol` y
  renderiza `HomeDocente` si es `"docente"`, o `InicioPlaceholder` para los otros dos roles
  (hasta que existan `US-ADJ-29`/`30`)
- [x] `frontend/src/router.tsx` — la ruta índice (`index: true`) pasa de
  `<InicioPlaceholder />` a `<Inicio />`

**Estado:** 0/2 tareas completadas
