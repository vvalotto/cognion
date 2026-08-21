# Plan de Implementación: US-2.2.9 - Login refleja el estado de cuenta bloqueada (UI)

**Patrón:** Clean Architecture BC-first (frontend puro — sin cambios de backend)
**Producto:** frontend

## Gap detectado en Fase 2

La spec (`docs/specs/inc2/US-2.2.9.md`, artefacto `frontend/src/lib/auth-api.ts`) asume un
archivo que no existe: `Login.tsx` (`frontend/src/pages/Login.tsx`) llama `apiFetch` de
`api-client.ts` directamente, sin una capa `auth-api.ts` intermedia. El backend
(`src/identidad/frameworks/api/auth_router.py`, ya implementado en `US-2.2.1`) ya distingue
las dos condiciones por status HTTP — 403 `CuentaBloqueadaError` vs. 401
`CredencialesInvalidas` — sin necesidad de un código de error adicional en el body.
**Decisión:** no crear `auth-api.ts`. Distinguir el caso directamente en `Login.tsx`
inspeccionando `ApiError.status` (ya expuesto por `api-client.ts`, mismo patrón que
`US-2.2.8` usó para `intentos_restantes`). Ningún archivo de `src/` se modifica.

## Componentes a Implementar

### 1. Alerta de cuenta bloqueada (Frontend)
- [ ] `frontend/src/pages/LoginCuentaBloqueadaError.tsx`
  - Componente de alerta destructiva, mismo patrón visual que `LoginError.tsx`
  - Texto: "Cuenta bloqueada" + indicación de contactar a un Administrador
    (`wireframes-cuentas-administracion.md` §2.8)

### 2. Integración en Login (Frontend)
- [ ] `frontend/src/pages/Login.tsx`
  - Nuevo estado `bloqueada: boolean` (además del `error` genérico existente)
  - En el `catch`, si `err instanceof ApiError && err.status === 403` → `setBloqueada(true)`
    (no limpiar el password, no queda nada que reintentar)
  - Si `err.status === 401` → comportamiento sin cambios de `US-1.1.7` (mensaje genérico)
  - Renderizar `LoginCuentaBloqueadaError` en vez de `LoginError` cuando `bloqueada === true`
  - Deshabilitar los campos `email`/`password` y el botón "Ingresar" cuando `bloqueada === true`
    (`fieldset disabled` o prop `disabled` en cada control)

**Estado:** 0/2 tareas completadas
