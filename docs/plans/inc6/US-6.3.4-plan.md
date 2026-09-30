# Plan de Implementación: US-6.3.4 - Infraestructura de frontend del modo en vivo

**Patrón:** React 19 + TypeScript + Vite (frontend), sobre `api-client.ts`/`session.ts`/`RequireRole` ya existentes
**Producto:** Cognion — frontend

## Decisión de diseño (Fase 2)

- **Cliente API:** mismo patrón manual snake_case↔camelCase que `actividad-evaluativa-api.ts`
  (interfaces `*ApiResponse` internas con snake_case + funciones `mapear*` explícitas) — sin
  conversor genérico, consistente con todo `lib/*-api.ts` del proyecto.
- **Canal WebSocket:** módulo nuevo `canal-sesion-en-vivo.ts` con una clase/factory
  `CanalSesionEnVivo` que envuelve el `WebSocket` nativo — inyectable (constructor recibe un
  `WebSocketFactory` opcional, default `(url) => new WebSocket(url)`) para poder testear con un
  fake en Vitest (`jsdom` no trae un `WebSocket` funcional).
- **Hook `useCanalSesionEnVivo`:** crea el canal **dentro de `useEffect`**, lo cierra en el
  cleanup — lección de `US-ADJ-20`/`US-4.1.x` (recurso creado en el render se rompe con el
  doble montaje de `StrictMode`, invisible a Vitest). Se verifica además en `npm run dev` real.
- **`StageLayout`:** análogo a `AppLayout` pero sin `TopStrip`/`AppNav`/`Footer`/`UserMenu`,
  fondo `--stage-bg`, solo `<Outlet />`.
- **Tokens `--stage-*`:** bloque `:root` propio en `index.css`, **no** parte de los bloques
  `:root`/`.dark` existentes (la proyección no cambia con el tema de la app — siempre oscura,
  criterio ya definido en `wireframes-actividad-evaluativa-en-vivo.md` §1.1).

## Componentes a Implementar

### 1. Cliente API

- [ ] `frontend/src/lib/sesion-en-vivo-api.ts` (nuevo)
  - Interfaces `*ApiResponse` (snake_case, internas) + tipos públicos (camelCase)
  - 12 funciones: `crearSesion`, `iniciarSesion`, `mostrarOpciones`, `cerrarPregunta`,
    `avanzarPregunta`, `finalizarSesion`, `unirseASesion`, `responderPregunta`,
    `obtenerEstadoSesion`, `listarParticipantes`, `obtenerRankingSesion`,
    `listarSesionesEnVivo` — todas sobre `apiFetch` de `api-client.ts`, sin manejo propio de
    401/403 (ya lo hace `apiFetch`)

### 2. Canal WebSocket

- [ ] `frontend/src/lib/canal-sesion-en-vivo.ts` (nuevo)
  - Tipos discriminados por `tipo` (los 6 de la tabla de la spec), mapeo snake_case→camelCase
  - `CanalSesionEnVivo`: conecta a `WS /sesiones-en-vivo/{id}/canal?token=<jwt>` (URL derivada
    de `VITE_API_BASE_URL`, `http`→`ws`/`https`→`wss`), reconexión con backoff exponencial
    (1, 2, 4, 8, tope 10 s), cierre `1008` → limpia sesión y navega a `/login` sin reintentar,
    mensaje de `tipo` desconocido se ignora, estado observable `conectado`/`reconectando`/
    `desconectado`
- [ ] `frontend/src/lib/use-canal-sesion-en-vivo.ts` (nuevo)
  - `useCanalSesionEnVivo(sesionId, onMensaje, onReconectado)` — crea/cierra el canal en
    `useEffect`, expone el estado de conexión

### 3. Layout y estilos

- [ ] `frontend/src/layouts/StageLayout.tsx` (nuevo) — sin `AppLayout`, fondo oscuro
- [ ] `frontend/src/index.css` — tokens `--stage-bg/fg/muted/accent/primary` + colores de
  opción `a/b/c/d` (valores del prototipo: `#0f1b24`, `#ffffff`, `#9fb3c0`, `#6fe39a`,
  `#4fb4f0`, `#c93a3e`/`#2f8fc7`/`#d9a324`/`#3f9463`)

### 4. Rutas

- [ ] `frontend/src/router.tsx` — 4 rutas nuevas (tabla de la spec), placeholders temporales en
  `frontend/src/pages/actividad-evaluativa/` (mismo criterio que `US-2.1.8`/`US-3.4.1`)

### 5. Integración

- [ ] Tests Vitest: `sesion-en-vivo-api.test.ts`, `canal-sesion-en-vivo.test.ts`,
  `use-canal-sesion-en-vivo.test.tsx`, ampliación de `router.test.tsx`
- [ ] `tests/features/inc6/US-6.3.4*.feature` — ya generado en Fase 1, validado contra Vitest
  (sin step_defs, mismo criterio que `US-2.1.8`/`US-3.4.1`)

**Estado:** 0/11 tareas completadas
