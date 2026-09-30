# Reporte de Implementación: US-6.3.4

## Resumen Ejecutivo

- **Historia de Usuario:** US-6.3.4 — Infraestructura de frontend del modo en vivo
- **Puntos estimados:** 5
- **Tiempo real:** ~159 min (tracker, Fases 0 a 9). Detalle en `.claude/tracking/US-6.3.4-tracking.json`
- **Estado:** ✅ COMPLETADO
- **Fecha completado:** 2026-09-22
- **Aporta:** primer uso de WebSockets del frontend — cliente API tipado, canal WebSocket con
  reconexión y backoff, hook de ciclo de vida seguro ante `StrictMode`, layout de proyección
  (`StageLayout`) con la paleta oscura `--stage-*`, y las 4 rutas del modo en vivo protegidas
  por rol con placeholders. Base sobre la que se construyen las seis US de pantallas siguientes
  (`US-6.3.5` a `US-6.3.9`).

---

## Componentes Implementados

### Cliente API (`frontend/src/lib/sesion-en-vivo-api.ts`, nuevo)

- ✅ 12 funciones tipadas sobre `apiFetch` (`api-client.ts`, `US-1.1.6`): `crearSesion`,
  `iniciarSesion`, `mostrarOpciones`, `cerrarPregunta`, `avanzarPregunta`, `finalizarSesion`,
  `unirseASesion`, `responderPregunta`, `obtenerEstadoSesion`, `listarParticipantes`,
  `obtenerRankingSesion`, `listarSesionesEnVivo`
- ✅ Mismo patrón que `actividad-evaluativa-api.ts`: interfaces `*ApiResponse` internas
  (snake_case) + tipos públicos camelCase + funciones `mapear*` explícitas, sin conversor
  genérico

### Canal WebSocket (`frontend/src/lib/canal-sesion-en-vivo.ts`, nuevo)

- ✅ **`CanalSesionEnVivo`** — conecta a `WS /sesiones-en-vivo/{id}/canal?token=<jwt>` (URL
  derivada de `VITE_API_BASE_URL`, `http`→`ws`/`https`→`wss`), tipos discriminados por `tipo`
  para los 6 mensajes del contrato (`participantes_actualizados`, `pregunta_presentada`,
  `opciones_mostradas`, `conteo_respuestas_actualizado`, `pregunta_cerrada`,
  `sesion_finalizada`), mapeo snake_case→camelCase
- ✅ Reconexión con backoff exponencial (1, 2, 4, 8, tope 10 s), dispara `onReconectado` al
  reconectar (la pantalla debe volver a pedir `GET estado`, nunca asumir que no se perdió un
  mensaje)
- ✅ Cierre `1008` (token inválido/vencido): no reintenta, limpia la sesión y navega a
  `/login` — mismo criterio que el 401 HTTP
- ✅ Mensaje con `tipo` desconocido o payload no-JSON se ignora sin romper (compatibilidad
  hacia adelante)
- ✅ `WebSocketFactory` inyectable (constructor, default `(url) => new WebSocket(url)`) —
  `jsdom` no trae un `WebSocket` funcional, necesario para testear con un fake en Vitest

### Hook (`frontend/src/lib/use-canal-sesion-en-vivo.ts`, nuevo)

- ✅ `useCanalSesionEnVivo(sesionId, onMensaje, onReconectado, crearWebSocket?)` — crea el
  canal **dentro de `useEffect`**, lo cierra en el cleanup (lección `US-ADJ-20`: un recurso con
  ciclo de vida creado en el render se rompe con el doble montaje de `StrictMode`, invisible a
  Vitest)
- ✅ `onMensaje`/`onReconectado` se leen vía `useRef` actualizado en cada render, para que el
  canal (creado una sola vez) siempre invoque el callback más reciente sin necesidad de
  recrear el socket

### Layout y estilos

- ✅ **`StageLayout.tsx`** (nuevo) — sin `AppLayout` (`TopStrip`/`AppNav`/`Footer`/`UserMenu`),
  fondo `--stage-bg`, solo `<Outlet />`
- ✅ **`index.css`** — bloque `:root` propio con los tokens `--stage-bg/fg/muted/accent/primary`
  y los 4 colores de opción (`--stage-color-a/b/c/d`), independiente de `:root`/`.dark`
  existentes — la proyección siempre es oscura, no sigue el tema del resto de la app
  (`wireframes-actividad-evaluativa-en-vivo.md` §1.1)

### Rutas (`frontend/src/router.tsx`)

| Ruta | Rol | Layout |
|---|---|---|
| `/sesiones-en-vivo/comisiones/:comisionId/nueva` | `docente` | `AppLayout` |
| `/sesiones-en-vivo/:sesionId/sala` | `docente` | `AppLayout` |
| `/sesiones-en-vivo/:sesionId/proyeccion` | `docente` | **`StageLayout`** |
| `/mis-sesiones-en-vivo/:sesionId` | `estudiante` | `AppLayout` |

- ✅ 4 placeholders temporales (`frontend/src/pages/actividad-evaluativa/_placeholders-en-vivo.tsx`),
  mismo criterio que `US-2.1.8`/`US-3.4.1`, hasta que `US-6.3.5` a `US-6.3.9` los reemplacen

---

## Sin gap de backend

Los 12 endpoints HTTP y el contrato de mensajes del canal ya estaban completamente
especificados en `docs/specs/inc6/US-6.3.4.md` (tabla de rutas backend confirmada contra
`sesiones_en_vivo_router.py`, shapes de request/response confirmados contra `schemas.py`) —
sin necesidad de decisiones nuevas con Víctor.

---

## Métricas de Calidad

| Métrica | Valor | Umbral (referencia) | Estado |
|---------|-------|----------------------|--------|
| oxlint | 0 errores (6 warnings preexistentes) | 0 errores | ✅ |
| `tsc -b` | 0 errores | 0 errores | ✅ |
| Vitest | 532/532 passed | 100% pasan | ✅ |
| Coverage archivos nuevos | 95–100% stmts | ≥80% | ✅ |
| Coverage global frontend | 91.96% stmts, 81.88% branches, 94.69% lines | ≥80% | ✅ |

Fuente: `quality/reports/inc6/US-6.3.4-quality.json`. Stack frontend — no aplican
pylint/CC/MI/CodeGuard (gates Python), adaptación documentada en
`docs/plans/inc6/US-6.3.4-context.md` (mismo criterio que `US-2.1.8`/`US-3.4.1`).

**Estado General:** ✅ APROBADO

---

## Tests Implementados

### Tests Unitarios
- `sesion-en-vivo-api.test.ts` (18 tests) — las 12 funciones del cliente: método HTTP, URL,
  body mapeado a snake_case, respuesta mapeada a camelCase, Authorization con el JWT de sesión
- `canal-sesion-en-vivo.test.ts` (8 tests) — tipado de los 6 mensajes del contrato, JSON
  inválido ignorado, mensaje de tipo desconocido ignorado, reconexión con `onReconectado`,
  backoff exponencial con tope de 10 s, cierre `1008` sin reintento (limpia sesión + navega a
  `/login`), `cerrar()` cierra el socket sin reintentar
- `use-canal-sesion-en-vivo.test.tsx` (6 tests) — canal creado dentro de `useEffect`
  (no en el render), sobrevive a un ciclo de unmount/remount sin sockets huérfanos, cleanup
  cierra el socket al desmontar, propaga mensaje y reconexión al callback más reciente

### Tests de Integración
- `router.test.tsx` (8 tests nuevos, describe `"Sesión en Vivo (US-6.3.4)"`) — cada ruta nueva
  redirige a `/login` sin sesión, renderiza con el rol correcto, rechaza con `RequireRole` el
  rol incorrecto (Estudiante en rutas de Docente y viceversa), la proyección usa `StageLayout`
  sin el menú de navegación (`screen.queryByRole("navigation")` ausente)

### Escenarios BDD (9 escenarios)
- `tests/features/inc6/US-6.3.4-infraestructura-frontend-modo-en-vivo.feature` — los 9
  escenarios de la spec, validados contra los tests Vitest de arriba (sin step_defs, mismo
  criterio frontend que `US-2.1.8`/`US-3.4.1`)

**Todos los tests pasando:** ✅ 532/532 (suite completa del frontend, sin regresiones)

---

## Archivos Creados/Modificados

### Código de producción
- `frontend/src/lib/sesion-en-vivo-api.ts` (nuevo)
- `frontend/src/lib/canal-sesion-en-vivo.ts` (nuevo)
- `frontend/src/lib/use-canal-sesion-en-vivo.ts` (nuevo)
- `frontend/src/layouts/StageLayout.tsx` (nuevo)
- `frontend/src/pages/actividad-evaluativa/_placeholders-en-vivo.tsx` (nuevo)
- `frontend/src/index.css` (tokens `--stage-*`)
- `frontend/src/router.tsx` (4 rutas nuevas)

### Tests
- `frontend/src/lib/sesion-en-vivo-api.test.ts` (nuevo)
- `frontend/src/lib/canal-sesion-en-vivo.test.ts` (nuevo)
- `frontend/src/lib/use-canal-sesion-en-vivo.test.tsx` (nuevo)
- `frontend/src/router.test.tsx` (ampliado)

### Documentación
- `docs/plans/inc6/US-6.3.4-context.md`, `US-6.3.4-plan.md`
- `docs/reports/inc6/US-6.3.4-report.md` (este archivo)
- `quality/reports/inc6/US-6.3.4-quality.json`
- `tests/features/inc6/US-6.3.4-infraestructura-frontend-modo-en-vivo.feature`
- `CHANGELOG.md` (entrada nueva bajo `[Unreleased]`)

---

## Criterios de Aceptación

- [x] Cliente API tipado con las 12 funciones, JWT/camelCase vía `apiFetch`
- [x] Canal WebSocket con reconexión, backoff exponencial con tope, cierre `1008` sin
      reintento, mensajes tipados y mapeados a camelCase, tipo desconocido ignorado
- [x] Hook `useCanalSesionEnVivo` seguro ante `StrictMode` — socket creado en `useEffect`,
      cerrado en el cleanup
- [x] `StageLayout` sin menú de navegación, con los tokens `--stage-*`
- [x] Las 4 rutas de la tabla existen, protegidas por rol, con placeholders

**Todos los criterios cumplidos:** ✅

---

## Próximos Pasos

- [ ] Cerrar Issue #415 con los SHAs de los commits de esta US
- [ ] Continuar con `US-6.3.5` (Docente: crear sesión + sala de espera) — primera pantalla real

---

## Lecciones Aprendidas

- ✅ Un `WebSocketFactory` inyectable en el constructor (default `(url) => new WebSocket(url)`)
  permite testear el canal completo con un fake en Vitest sin depender de un `WebSocket`
  funcional de `jsdom`.
- ⚠️ Un componente de prueba de React que llama a una función fábrica (`crearFactory()`) *dentro*
  de su cuerpo en cada render produce una nueva referencia en cada render — si esa referencia es
  una dependencia de `useEffect` (como `crearWebSocket` en este hook), el efecto se re-dispara en
  cada render, generando sockets/canales extra y falseando el test. Corregido moviendo la
  fábrica a una constante de módulo (`FACTORY`) fuera del componente. No es un bug del código de
  producción — es una trampa común al testear hooks con dependencias de función.
  `erasableSyntaxOnly` (`tsc -b`) rechaza el azúcar de *parameter properties* de TypeScript
  (`constructor(private readonly x: T)`) porque no es sintaxis erasable — hay que declarar los
  campos y asignarlos explícitamente en el cuerpo del constructor. Ya lo indicaba la lección
  `US-ADJ-23` sobre usar `tsc -b`, pero esta es la primera vez que el propio compilador señala
  esta regla específica.

---

**Reporte generado automáticamente por Claude Code**
**Fecha:** 2026-09-22
