# Plan de Implementación: US-ADJ-04 - Alinear visualmente Cuentas/Contraseñas con el prototipo

**Patrón:** React 19 + TypeScript + Vite (frontend puro, sin capas Clean Architecture)
**Producto:** cognion-frontend
**Estado:** ✅ COMPLETADO
**Fecha completado:** 2026-08-22
**Tiempo real (tracker):** 28 min (Fases 0 a 8)

Fuente de verdad UX: `docs/design/ux/prototipos/identidad-cuentas-administracion.html`
(mismos tokens que `banco-preguntas-carga-filtrado.html` — continuidad visual). Reutiliza las
primitivas ya creadas por `US-ADJ-01` (`Card`, `CardContent`, `Badge`, `Breadcrumb`, variante
`destructive-solid` de `Button`) — sin agregar componentes nuevos, solo variantes de `Badge`.

## Componentes a Implementar

### 1. Extensión de `Badge` (`US-ADJ-01`)

- [x] `frontend/src/components/ui/badge.tsx`
  - Variantes nuevas: `rol-docente` (azul), `rol-estudiante` (violeta), `rol-admin`
    (naranja), `estado-activa` (verde), `estado-bloqueada` (rojo) — mismo patrón `cva` que
    `tipo-om`/`nivel-alto`, sin tocar las variantes existentes de Banco de Preguntas

### 2. Pantallas — aplicar Card/Badge/Breadcrumb sin cambiar comportamiento

- [x] `frontend/src/pages/Cuentas.tsx`
  - Breadcrumb "Administración › Cuentas"
  - Filtros envueltos en `Card`; tabla envuelta en `Card`
  - Columna Rol con `Badge` (`rol-*`); columna Estado con `Badge` (`estado-*`)
  - Columna/botón "Ver" nuevo en cada fila (navega a `/cuentas/{id}`, misma ruta que hoy usa
    el click de la fila — se agrega sin quitar el click de fila existente, para no romper
    `Cuentas.test.tsx`)
- [x] `frontend/src/pages/CuentaDetalle.tsx`
  - Breadcrumb como componente (hoy es texto plano)
  - Bloque de datos envuelto en `Card`
  - Rol y Estado como `Badge` (reemplaza el texto plano "Activa"/"Bloqueada" — mismo texto,
    ahora dentro del componente)
- [x] `frontend/src/pages/ResetearPassword.tsx`
  - Breadcrumb como componente
  - Formulario envuelto en `Card`
  - Botón "Resetear contraseña" con variante `destructive-solid` (hoy `destructive` soft)
- [x] `frontend/src/pages/CuentaReseteada.tsx`
  - `Card` centrada (`result-card`) con ícono de éxito (✓), mismo tratamiento que las
    pantallas de éxito del prototipo
- [x] `frontend/src/pages/CambiarPassword.tsx`
  - Breadcrumb "Mi cuenta › Cambiar contraseña"
  - Formulario envuelto en `Card`
  - Pantalla de éxito como `Card` centrada con ícono, igual que `CuentaReseteada.tsx`

### 3. Ajuste de tests existentes

- [x] Revisar `Cuentas.test.tsx`, `CuentaDetalle.test.tsx`, `ResetearPassword.test.tsx`,
  `CuentaReseteada.test.tsx`, `CambiarPassword.test.tsx` — ajustar únicamente los selectors
  que dependan de la jerarquía DOM que cambia (queries por texto/rol no deberían romperse si
  el copy no cambia); agregar assertions para el botón "Ver" nuevo en `Cuentas.test.tsx`

**Estado:** 8/8 tareas completadas
