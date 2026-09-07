# Plan de Implementación: US-ADJ-27 - Menú de navegación persistente en AppLayout

**Patrón:** Frontend puro (sin capas de dominio — Clean Architecture BC-first no aplica)
**Producto:** cognion
**Estado:** ✅ COMPLETADO — 2/2 tareas, quality gates APROBADO
(`quality/reports/inc4-adj/US-ADJ-27-quality.json`)

## Componentes a Implementar

### 1. `AppNav.tsx` (componente nuevo)

- [x] `frontend/src/components/AppNav.tsx`
  - Recibe el rol vía `getSession()` (o prop `rol`, a decidir en implementación según el
    patrón ya usado por otros componentes de `components/`)
  - Tabla de ítems por rol (constante `ITEMS_POR_ROL: Record<Rol, {label, to}[]>`):
    - `docente`: Inicio (`/`), Banco de Preguntas (`/materias`), Actividades
      (`/actividad-evaluativa/materias`), Desempeño por alumno
      (`/analytics/desempeno-por-alumno`), Desempeño por tema
      (`/analytics/desempeno-por-tema`)
    - `estudiante`: Inicio (`/`), Mis Actividades (`/mis-actividades/materias`), Mi Desempeño
      (`/analytics/mi-desempeno`)
    - `administrador`: Inicio (`/`), Comisiones (`/comisiones`), Docentes (`/docentes/nuevo`),
      Cuentas (`/cuentas`)
  - Ítem activo: `useLocation()` de `react-router` — activo si
    `pathname === to || pathname.startsWith(to + "/")`, con caso especial para `to === "/"`
    (solo activo si `pathname === "/"`, para no marcar "Inicio" en todas las pantallas)
  - Usa `<Link>` de `react-router`, clase `current` en el ítem activo (mismo nombre que el
    prototipo `.app-nav a.current`)

### 2. Integración en `AppLayout.tsx`

- [x] `frontend/src/layouts/AppLayout.tsx`
  - Agrega `<AppNav />` debajo del `<header>`, solo si `getSession()` no es `null` (mismo
    guard que el badge de rol actual)

**Estado:** 0/2 tareas completadas
