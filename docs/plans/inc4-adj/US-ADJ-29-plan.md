# Plan de Implementación: US-ADJ-29 - Home del Estudiante

**Patrón:** Frontend puro (sin capas de dominio)
**Producto:** cognion
**Estado:** ✅ COMPLETADO — 2/2 tareas, quality gates APROBADO
(`quality/reports/inc4-adj/US-ADJ-29-quality.json`)

## Componentes a Implementar

### 1. `HomeEstudiante.tsx` (pantalla nueva)

- [x] `frontend/src/pages/HomeEstudiante.tsx`
  - Mismo patrón que `HomeDocente.tsx`: sin breadcrumb, `<h1>Hola, Estudiante</h1>`, grid de
    `Card` con `role="button"` + `onClick`/`onKeyDown`
  - 2 cards:
    - Mis Actividades → `/mis-actividades/materias`
    - Mi Desempeño → `/analytics/mi-desempeno`

### 2. Rama `estudiante` en `Inicio.tsx`

- [x] `frontend/src/pages/Inicio.tsx` — agrega `if (rol === "estudiante") return <HomeEstudiante />`

**Estado:** 0/2 tareas completadas
