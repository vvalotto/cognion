# Plan de Implementación: US-2.2.8 - Cualquier usuario autenticado cambia su propia contraseña (UI)

**Patrón:** Clean Architecture BC-first (backend) + React/TS sin capas (frontend)
**Producto:** cognion

## Gaps detectados en Fase 2 (antes de escribir código)

1. **`intentos_fallidos_password` no expuesto en el error.** El backend de `US-2.2.5`
   (`PUT /usuarios/me/password`) devuelve `detail` como string genérico
   ("La contraseña actual es incorrecta.") sin el contador que la spec de esta US da por
   expuesto. Decisión de Víctor: **extender el backend** — la US pasa a tocar
   `src/` además de `frontend/`.
2. **Conflicto de contrato con el interceptor global de 401.** `api-client.ts` trata
   *cualquier* respuesta 401 como sesión inválida: limpia la sesión y navega a `/login`
   (`US-1.1.6`). El endpoint de `US-2.2.5` devuelve 401 en `PasswordActualIncorrecta` — si el
   frontend usa `apiFetch` sin ajuste, el criterio "no requiere volver a iniciar sesión" se
   rompe (el usuario terminaría deslogueado en el propio error de contraseña incorrecta).
   Resuelto en frontend, sin tocar el código de estado HTTP del backend (401/403 ya está
   testeado por `US-2.2.5` — cambiarlo ampliaría el alcance y el riesgo más allá de esta US):
   `apiFetch` gana una opción `handleUnauthorized` (default `true`, sin cambiar ningún caller
   existente) que esta pantalla usa en `false`.

## Componentes a Implementar

### 1. Backend — exponer intentos restantes (extensión mínima sobre `US-2.2.5`)

- [x] `src/identidad/entities/usuario.py`
  - Método `intentos_restantes_cambio_password() -> int`: `max(0, 3 - intentos_fallidos_password)`,
    reutiliza `_INTENTOS_MAXIMOS_CAMBIO_PASSWORD` ya existente (INV-ID-10)
- [x] `src/identidad/entities/errors.py`
  - `PasswordActualIncorrecta` gana el atributo `intentos_restantes: int | None = None`
    (mismo patrón ya usado para `evento_cuenta_bloqueada`)
- [x] `src/identidad/use_cases/cambiar_password.py`
  - Tras `registrar_fallo_cambio_password()`, fija `exc.intentos_restantes =
    usuario.intentos_restantes_cambio_password()`
- [x] `src/identidad/frameworks/api/perfil_router.py`
  - `except PasswordActualIncorrecta`: siempre 401 (**corrección durante Fase 3** — el plan
    original proponía 403 para el 3er fallo, pero rompía el contrato ya testeado de
    `US-2.2.5`: `test_us_2_2_5_steps.py` afirma `status_code == 401` incluso cuando el fallo
    bloquea la cuenta). El `detail` distingue el caso: `{"mensaje", "bloqueada": true}` si
    `exc.evento_cuenta_bloqueada` está seteado (3er fallo, cuenta recién bloqueada);
    `{"mensaje", "intentos_restantes"}` en cualquier otro fallo
  - `except CuentaBloqueadaError` (cuenta ya estaba bloqueada *antes* de este intento,
    status 403 sin cambios): `detail={"mensaje": str(exc), "bloqueada": True}` — mismo shape
    de `bloqueada` que el 401 de arriba, para que el frontend use una sola rama de manejo
  - Sin cambio de status codes existentes de `US-2.2.5` (401/403/422) — solo cambia la forma
    del `detail`, de string a objeto

Backend completo: `x/4` → **4/4 tareas backend completadas.**

### 2. Frontend — cliente API

- [x] `frontend/src/lib/api-client.ts`
  - `ApiError` gana `detail?: unknown` (cuerpo estructurado del error, si lo hay)
  - `ApiFetchOptions` gana `handleUnauthorized?: boolean` (default `true` — no cambia ningún
    caller existente)
  - Si `handleUnauthorized === false` y la respuesta es 401: no limpia sesión ni navega a
    `/login`, solo lanza `ApiError` con `message`/`detail`
- [x] `frontend/src/lib/cuentas-api.ts`
  - `CambiarPasswordError` (clase, extiende `Error`): `mensaje`, `intentosRestantes?: number`,
    `bloqueada: boolean`
  - `cambiarPassword(passwordActual, passwordNueva): Promise<void>` — `PUT
    /usuarios/me/password` con `handleUnauthorized: false`; en el catch, si `ApiError.detail`
    trae la forma estructurada, relanza `CambiarPasswordError` mapeando snake_case→camelCase

### 3. Frontend — pantalla

- [x] `frontend/src/pages/CambiarPassword.tsx`
  - Un solo componente con 3 estados internos: `formulario` (default) / `error` (alerta
    destructiva con intentos restantes o mensaje de bloqueo) / `exito` (confirmación,
    aclara que la sesión sigue activa, botón "Continuar" → `navigate(-1)`)
  - Validación de cliente antes de llamar al backend: nueva ≥ 8 caracteres, coincidencia
    nueva/confirmación (mismo patrón que `ResetearPassword.tsx`)
  - Catch de `CambiarPasswordError`: `bloqueada` → mensaje de cuenta bloqueada, contactar
    Administrador; si no, alerta con `intentosRestantes` y limpieza de los 3 campos

### 4. Integración

- [x] `frontend/src/router.tsx`
  - Ruta `/mi-cuenta/cambiar-password` dentro de `AppLayout`, **sin** `RequireRole` — accesible
    a cualquier rol autenticado (a diferencia del resto de rutas de la Iteración 2)
  - Sin entrada de navegación nueva (no hay menú en `AppLayout` todavía — mismo estado que el
    resto de las pantallas post-login; fuera de alcance de esta US)

**Estado:** ✅ COMPLETADO
**Fecha completado:** 2026-08-20

## Métricas de Tiempo

| Fase | Elapsed |
|------|---------|
| Fase 0 — Validación de Contexto | 62s |
| Fase 1 — Escenarios BDD | 970s |
| Fase 2 — Plan de Implementación | 573s |
| Fase 3 — Implementación (8 tareas) | 791s |
| Fase 4 — Tests Unitarios | 510s |
| Fase 5 — Tests de Integración (suite completa backend 357/357 + Vitest 145/145) | 105s |
| Fase 6 — Validación BDD | 149s |
| Fase 7 — Quality Gates | 783s |
| **Total (Fases 0–7)** | **~67 min** |

## Lecciones Aprendidas

- ⚠️ El plan original (Fase 2) proponía 403 para el 3er fallo consecutivo de
  `PasswordActualIncorrecta`, pero eso rompía el contrato ya testeado de `US-2.2.5`
  (`test_us_2_2_5_steps.py` afirma 401 incluso cuando el fallo bloquea la cuenta). Se detectó
  recién al correr esa suite en Fase 3, no en la planificación — para extensiones sobre un
  endpoint ya shippeado, correr su suite de tests *antes* de escribir el código nuevo (no
  solo al final) habría anticipado el ajuste.
- ✅ Resolver el conflicto con el interceptor global de 401 (`apiFetch`) agregando
  `handleUnauthorized: false` como opción, en vez de cambiar el status code del backend,
  mantuvo el contrato de `US-2.2.5` intacto y acotó el riesgo de esta extensión a un único
  archivo frontend (`api-client.ts`) sin tocar ningún caller existente.
- 💡 Exponer `intentos_restantes` como atributo mutable post-construcción en la excepción de
  dominio (mismo patrón que `evento_cuenta_bloqueada` de `US-2.2.1`) evitó tener que rediseñar
  la firma de `PasswordActualIncorrecta()` — consistente con el estilo ya establecido en el BC.
