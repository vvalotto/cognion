# Plan de Implementación: US-ADJ-30 - Home del Administrador

**Patrón:** Frontend puro (sin capas de dominio)
**Producto:** cognion
**Estado:** ✅ COMPLETADO — 3/3 tareas, quality gates APROBADO
(`quality/reports/inc4-adj/US-ADJ-30-quality.json`). Cierra completa la Iteración 1b del
Incremento 4-ADJ.

## Componentes a Implementar

### 1. `HomeAdministrador.tsx` (pantalla nueva)

- [x] `frontend/src/pages/HomeAdministrador.tsx`
  - Mismo patrón que `HomeDocente.tsx`/`HomeEstudiante.tsx`
  - 3 cards:
    - Comisiones → `/comisiones`
    - Alta de Docente → `/docentes/nuevo`
    - Cuentas → `/cuentas`

### 2. Rama `administrador` en `Inicio.tsx`

- [x] `frontend/src/pages/Inicio.tsx` — agrega `if (rol === "administrador") return <HomeAdministrador />`

### 3. `RUTA_POST_LOGIN` en `Login.tsx`

- [x] `frontend/src/pages/identidad/Login.tsx` — con los 3 roles navegando a `"/"`, la tabla
  `RUTA_POST_LOGIN` quedó redundante; se eliminó y `navigate(RUTA_POST_LOGIN[response.rol])`
  pasó a `navigate("/")` directo (simplificación, consecuencia directa del cambio pedido)

**Estado:** 0/3 tareas completadas
