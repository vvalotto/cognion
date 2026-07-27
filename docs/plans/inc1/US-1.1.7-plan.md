# Plan de Implementación: US-1.1.7 - Docente/Administrador/Estudiante inicia sesión desde la UI

**Patrón:** React 19 + TypeScript + Vite (sin capas Clean Architecture — no aplica a `frontend/`)
**Producto:** cognion (frontend)

## Componentes a Implementar

### 1. Componentes UI base (shadcn/ui)
- [x] `frontend/src/components/ui/input.tsx` — vía `npx shadcn add input` (mismo mecanismo usado para `button.tsx`, `cef8abb`)
- [x] `frontend/src/components/ui/label.tsx` — vía `npx shadcn add label`

### 2. Pantallas de Login (`frontend/src/pages/`)
- [x] `LoginError.tsx`
  - Componente presentacional — alerta destructiva con el mensaje fijo del wireframe (§2.2):
    "Email o contraseña incorrectos" / "Verificá tus datos e intentá de nuevo."
  - Sin lógica propia — recibe control del padre (`Login.tsx`) sobre cuándo renderizarse.
- [x] `Login.tsx`
  - Formulario controlado: `email`, `password` (campos shadcn `Input` + `Label`, botón "Ingresar").
  - Envío: `apiFetch<LoginResponse>("/identidad/login", { method: "POST", body: { email, password } })`.
  - Éxito (200): `setSession({ token: access_token, rol })`, navega según rol:
    - `administrador` → `/docentes/nuevo` (ruta que llega US-1.1.9; no se implementa acá)
    - `docente` / `estudiante` → `/` (placeholder de `AppLayout`, punto 3)
  - Error (`ApiError`, cualquier status — en la práctica 401 `CredencialesInvalidas`):
    limpia el campo `password`, mantiene `email`, renderiza `<LoginError />` dentro de la misma
    tarjeta (no es una ruta separada — el wireframe mantiene `/login` como una sola pantalla con
    dos estados, §2.2: "los campos se mantienen... la contraseña se re-solicita vacía").

### 3. Placeholder post-login (Docente/Estudiante)
- [x] `frontend/src/pages/_placeholders.tsx`
  - Agregar `InicioPlaceholder` ("Sesión iniciada — pendiente de pantalla propia") — destino de
    la redirección para `docente`/`estudiante` hasta que existan sus pantallas propias
    (incrementos futuros, fuera de alcance de esta US).
  - Quitar `LoginPlaceholder` (reemplazado por la pantalla real).

### 4. Integración
- [x] `frontend/src/router.tsx`
  - Reemplazar `LoginPlaceholder` por `Login` en la ruta `/login` (dentro de `AuthLayout`).
  - Agregar ruta `index` con `InicioPlaceholder` dentro de `AppLayout` (hoy sin `children`).

**Estado:** 6/6 tareas completadas
