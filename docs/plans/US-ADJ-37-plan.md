# Plan de Implementación: US-ADJ-37 - Descubribilidad: menú de usuario (cambiar contraseña, cerrar sesión)

**Patrón:** Frontend puro (React + TypeScript) — no aplica Clean Architecture BC-first (sin backend)
**Producto:** cognion

## Componentes a Implementar

### 1. Componente `UserMenu` (nuevo, `frontend/src/components/`)
- [ ] `frontend/src/components/UserMenu.tsx`
  - Envuelve el primitivo `Menu` de `@base-ui/react/menu` (mismo criterio que `components/ui/button.tsx`
    envolviendo `@base-ui/react/button`: primitivo sin estilar + clases Tailwind del proyecto)
  - `Menu.Root` → `Menu.Trigger` (reemplaza el `<div>` estático de avatar/nombre) → `Menu.Portal` →
    `Menu.Positioner` → `Menu.Popup`
  - Trigger: mismo markup visual que hoy (avatar circular con iniciales + nombre + rol), agrega un
    ícono de caret (`ChevronDown` de `lucide-react`, ya usado en `select.tsx`)
  - Popup: encabezado con nombre + rol (mismo dato ya calculado en `AppLayout.tsx` — sin agregar
    email, dato no disponible client-side; mismo criterio que `US-ADJ-28`/`29`/`30`, saludo genérico
    sin `GET /usuarios/me`), separador, dos `Menu.Item`:
    - "🔑 Cambiar contraseña" → `Menu.Item render` con un `Link` de `react-router` a
      `/mi-cuenta/cambiar-password`
    - "↩ Cerrar sesión" → `Menu.Item onClick` que llama `clearSession()` (`@/lib/session`) y
      `navigate("/login")` (`useNavigate` de `react-router`)
  - Props: recibe `nombre: string | null` y `rol: Rol` (mismos datos que `AppLayout.tsx` ya calcula)
    — sin leer `session`/`localStorage` directamente, mismo patrón que `AppNav` (recibe `rol` por prop)

### 2. Integración en `AppLayout.tsx`
- [ ] `frontend/src/layouts/AppLayout.tsx`
  - Reemplaza el bloque `<div className="flex items-center gap-2 ...">` (líneas 35-44, avatar+nombre
    estático) por `<UserMenu nombre={nombre} rol={session.rol} />`
  - Sin cambios en `TopStrip`, `AppNav`, `Footer` ni en la lógica de `iniciales()`/`ETIQUETA_ROL`
    (se mueven a `UserMenu.tsx` junto con el trigger, ya que son datos de presentación del propio menú)

**Fuera de alcance:** `CambiarPassword.tsx`, `clearSession()`, rutas de `router.tsx` — todo ya existe
y funciona; esta US solo agrega el punto de entrada por clic.

**Estado:** ✅ COMPLETADO — 2/2 tareas completadas
**Fecha completado:** 2026-09-12
**Tiempo real:** ~10 min de tracking (Fases 0, 2-5, 7-9). Detalle completo en
`docs/reports/inc5-adj/US-ADJ-37-report.md`.
