# Plan de Implementación: US-ADJ-40 - Pantallas de recuperación de contraseña

**Patrón:** Frontend puro (React + TypeScript + Vite), sin capas `entities/use_cases/interface_adapters/frameworks` — no aplica Clean Architecture backend a esta US.
**Producto:** cognion (frontend)
**Estado:** ✅ COMPLETADO
**Fecha completado:** 2026-09-13
**Tiempo real:** ~34 min (Fases 0–8, `tracker_cli.py status`)

## Decisión de diseño — distinguir errores del `POST .../confirmar` sin código de error estructurado

`POST /identidad/recuperar-password/confirmar` (`US-ADJ-39`) responde 422 con `detail` como
**string plano** (`str(exc)`), no como objeto `{mensaje, ...}` (a diferencia de
`CambiarPasswordError`). `extractError` (`api-client.ts`) ya maneja ese caso: cuando `detail`
es string, `ApiError.message` queda con el texto exacto de la excepción de dominio y
`ApiError.detail` queda `undefined`.

Las 5 excepciones (`src/identidad/entities/errors.py`) dan dos familias de mensaje
distinguibles por prefijo:
- Política de contraseña (`PasswordDemasiadoCorta`/`PasswordSinComplejidadSuficiente`):
  `"La contraseña debe..."`
- Token (`TokenRecuperacionInvalido`/`Vencido`/`YaUsado`): `"El token de recuperación '...'..."`

**Decisión:** sin agregar una clase de error nueva a `cuentas-api.ts` (no hace falta más
estructura que la que ya da `ApiError.message`) — `RecuperarPasswordNueva.tsx` decide la
navegación con `err.message.startsWith("La contraseña")`. Encapsulado en un helper local
`esErrorPoliticaPassword(mensaje: string)` en el propio componente para que el criterio quede
en un solo lugar y sea fácil de mover si el backend estructura el error más adelante.

## Componentes a Implementar

### 1. Cliente API — `frontend/src/lib/cuentas-api.ts`
- [x] `solicitarRecuperacionPassword(email: string, signal?: AbortSignal): Promise<void>`
  - `POST /identidad/recuperar-password/solicitar`, sin JWT (endpoint público — `apiFetch` ya
    omite el header `Authorization` si no hay sesión, sin cambios necesarios en `apiFetch`)
  - Responde 202 sin body relevante — no hace falta parsear nada distinto de éxito/error
- [x] `confirmarNuevaPassword(token: string, passwordNueva: string, signal?: AbortSignal): Promise<void>`
  - `POST /identidad/recuperar-password/confirmar`, sin JWT
  - Propaga `ApiError` tal cual (sin envolver) — el criterio de distinción de errores vive en
    el componente, no en el cliente

### 2. Pantallas nuevas — `frontend/src/pages/identidad/`
- [x] `RecuperarPasswordSolicitar.tsx` (ruta `/recuperar-password`, wireframe §4.1)
  - Campo Email (`Input` estándar, no `PasswordInput`)
  - Botón "Enviar link de recuperación" → `solicitarRecuperacionPassword(email)`
  - Siempre navega a `/recuperar-password/solicitado` al responder (202) — sin manejar error
    del backend como caso distinto, ya que el endpoint no devuelve 4xx por email inexistente
    (INV-ID-17); solo un error de red/500 real se deja propagar (mismo patrón que otras
    pantallas: no capturar lo que no es un caso de negocio)
  - Link "‹ Volver a iniciar sesión" → `/login`
- [x] `RecuperarPasswordSolicitado.tsx` (ruta `/recuperar-password/solicitado`, wireframe §4.2)
  - Mensaje genérico + aclaración de vigencia (1 hora)
  - Botón "Volver a iniciar sesión" → `/login`
  - Sin estado ni props — pantalla estática, mismo patrón que `RegistroExito.tsx`/`RegistroError.tsx`
- [x] `RecuperarPasswordNueva.tsx` (ruta `/recuperar-password/:token`, wireframe §4.3)
  - `token` desde `useParams()` (path param, no query — a diferencia de `Registro.tsx`, que usa
    `?token=`; se sigue la spec/tabla de artefactos literalmente, que fija esta ruta)
  - Dos `PasswordInput`: "Contraseña nueva" (`mostrarFortaleza`, `minLength={12}`) y "Confirmar
    contraseña nueva" — sin campo de contraseña actual (a diferencia de `CambiarPassword.tsx`)
  - Validación de cliente antes del submit: longitud ≥ 12 y coincidencia entre ambos campos
    (mismo patrón que `Registro.tsx`/`CambiarPassword.tsx` — error inline, sin llamar al
    backend)
  - Éxito → navega a `/recuperar-password/exito`
  - Error con `esErrorPoliticaPassword(err.message)` → error inline, formulario se mantiene
  - Cualquier otro `ApiError` (familia de token) → navega a `/recuperar-password/invalido`
  - Mismo patrón de `AbortController` en `useEffect` que `Login.tsx`/`Registro.tsx`/
    `CambiarPassword.tsx` (`US-ADJ-20`, fix de `StrictMode`)
- [x] `RecuperarPasswordTokenInvalido.tsx` (ruta `/recuperar-password/invalido`, wireframe §4.4)
  - Mensaje "Este link ya no es válido" + explicación (vigencia 1h, un solo uso)
  - Sin formulario de contraseña
  - Link "Pedir un nuevo link" → `/recuperar-password`
- [x] `RecuperarPasswordExito.tsx` (ruta `/recuperar-password/exito`, wireframe §4.5)
  - Confirmación + botón "Iniciar sesión" → `/login`

### 3. Modificación — `frontend/src/pages/identidad/Login.tsx`
- [x] Agrega link "¿Olvidaste tu contraseña?" en el `fieldset` del formulario, junto al botón
  "Ingresar" (wireframe §3.1) — navega a `/recuperar-password`. Único cambio a este archivo
  (fuera de alcance cualquier otro ajuste, según la spec).

### 4. Integración — `frontend/src/router.tsx`
- [x] 5 rutas nuevas bajo el mismo `AuthLayout` público que `/login`/`/registro*`, sin
  `RequireRole`:
  - `/recuperar-password` → `RecuperarPasswordSolicitar`
  - `/recuperar-password/solicitado` → `RecuperarPasswordSolicitado`
  - `/recuperar-password/:token` → `RecuperarPasswordNueva`
  - `/recuperar-password/invalido` → `RecuperarPasswordTokenInvalido`
  - `/recuperar-password/exito` → `RecuperarPasswordExito`
  - (la spec menciona "3 rutas nuevas" pero lista 5 pantallas — se registran las 5, una ruta
    por pantalla, mismo criterio que `/registro`, `/registro/error`, `/registro/exito`)

**Estado:** 9/9 tareas completadas
