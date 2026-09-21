# US-6.3.4: Infraestructura de frontend del modo en vivo

**Estado**: `Especificada`
**Iteracion / Sprint**: `INC-6.3`
**Tipo**: `feat frontend` (técnica)
**Agregado principal afectado**: — (soporte técnico, sin lógica de dominio propia)
**Bounded Context**: Actividad Evaluativa

---

## Descripcion (lenguaje de negocio)

Como **equipo de desarrollo**,
quiero **el cliente API, el canal WebSocket y las rutas del modo en vivo montados en el frontend**,
para **tener la base sobre la que se construyen las seis US de pantallas siguientes (`US-6.3.5` a `US-6.3.9`)**.

---

## Contexto del dominio

### Problema

Es el **primer uso de WebSockets del frontend**: no existe ninguna conexión persistente en `frontend/src/`. El
cliente HTTP (`api-client.ts`, JWT, 401/403), `RequireRole` y el patrón de rutas placeholder ya existen y se
reutilizan sin cambios (mismo criterio que `US-2.1.8` y `US-3.4.1`).

### Modelo involucrado

| Elemento | Nombre | Responsabilidad |
|---|---|---|
| Cliente API (nuevo) | `lib/sesion-en-vivo-api.ts` | Funciones tipadas (camelCase) para todos los endpoints de `/sesiones-en-vivo`: `crearSesion`, `iniciarSesion`, `mostrarOpciones`, `cerrarPregunta`, `avanzarPregunta`, `finalizarSesion`, `unirseASesion`, `responderPregunta`, `obtenerEstadoSesion`, `listarParticipantes`, `obtenerRankingSesion`, `listarSesionesEnVivo` |
| Canal (nuevo) | `lib/canal-sesion-en-vivo.ts` | Conexión WebSocket a `WS /sesiones-en-vivo/{id}/canal?token=<jwt>`: tipos de mensaje, reconexión y aviso de re-sincronización |
| Hook (nuevo) | `lib/use-canal-sesion-en-vivo.ts` | `useCanalSesionEnVivo(sesionId, onMensaje, onReconectado)` — ciclo de vida seguro |
| Layout (nuevo) | `layouts/StageLayout.tsx` | Layout de **proyección**: sin `AppLayout`/menú, fondo oscuro con los tokens `--stage-*` de `wireframes…-en-vivo.md` §1.1 |
| Estilos | `index.css` | Tokens `--stage-*` (bg, fg, muted, accent, primary) y colores de opción `a/b/c/d` |
| Rutas | `router.tsx` | Ver tabla |
| Placeholders | `pages/actividad-evaluativa/…` | Temporales, hasta que `US-6.3.5` a `US-6.3.9` los reemplacen (mismo criterio que `US-2.1.8`) |

### Rutas nuevas

| Ruta | Rol (`RequireRole`) | Layout | La implementa |
|---|---|---|---|
| `/sesiones-en-vivo/comisiones/:comisionId/nueva` | `docente` | `AppLayout` | `US-6.3.5` |
| `/sesiones-en-vivo/:sesionId/sala` | `docente` | `AppLayout` | `US-6.3.5` |
| `/sesiones-en-vivo/:sesionId/proyeccion` | `docente` | **`StageLayout`** | `US-6.3.6`, `US-6.3.7` |
| `/mis-sesiones-en-vivo/:sesionId` | `estudiante` | `AppLayout` | `US-6.3.8`, `US-6.3.9` |

### Contrato del canal (lo que ya emite el backend)

Solo **servidor → cliente** (los comandos van por HTTP, `ADR-005`). Unión discriminada por `tipo`:

| `tipo` | Campos |
|---|---|
| `participantes_actualizados` | `cantidad`, `participantes[{estudianteId, nombre, unidoEn}]` |
| `pregunta_presentada` | `preguntaActualIndice`, `pregunta{preguntaId, enunciado, tipo}` |
| `opciones_mostradas` | `preguntaActualIndice`, `opciones: string[] \| null`, `tiempoLimitePorPreguntaSegundos`, `cantidadRespuestas` |
| `conteo_respuestas_actualizado` | `preguntaActualIndice`, `cantidadRespuestas` |
| `pregunta_cerrada` | `preguntaActualIndice`, `respuestaCorrecta{contenido, texto, opciones}`, `distribucion[{opcion, cantidad}]`, `ranking[{posicion, estudianteId, nombre, puntajeAcumulado}]` |
| `sesion_finalizada` | `ranking[{posicion, estudianteId, nombre, puntajeAcumulado}]` |

Los mensajes llegan en snake_case; el canal los mapea a camelCase (mismo criterio que el resto de `lib/*-api.ts`).
`distribucion.opcion` es el índice como texto (`"0"`…) o `"verdadero"`/`"falso"`.

### Comportamiento del canal (reglas de diseño)

- **URL derivada de `VITE_API_BASE_URL`** (`http`→`ws`, `https`→`wss`); el token se toma de la sesión guardada.
- **Reconexión** con backoff exponencial (1 s, 2 s, 4 s … tope 10 s). Al **reconectar** dispara `onReconectado` para
  que la pantalla vuelva a pedir `GET estado` y **recalcule su etapa** — nunca se asume que no se perdió un mensaje.
- **Cierre `1008`** (token inválido/vencido): no reintenta; limpia la sesión y navega a `/login` (mismo criterio que el 401 HTTP).
- Estado observable: `conectado` | `reconectando` | `desconectado`, para el indicador de `US-6.3.0` H8.
- **Seguro ante StrictMode:** el socket se crea **dentro de `useEffect`** y se cierra en el cleanup. Es la lección de
  `US-ADJ-20`: crear un recurso con ciclo de vida en el render lo rompe con el doble montaje de desarrollo, invisible
  a Vitest. **Se verifica en `npm run dev` real**, no solo con tests.
- Un mensaje con `tipo` desconocido se **ignora sin romper** (compatibilidad hacia adelante).

---

## Especificacion del comportamiento

### Precondicion

- `US-6.3.1` cerrada (los tipos incluyen `nombre`); `US-6.3.0` no bloquea esta US (no hay pantallas).

### Postcondicion

- Las rutas de la tabla existen, protegidas por rol, con placeholders.
- El canal se conecta, recibe, se reconecta y avisa la re-sincronización; ningún caller nuevo necesita manejar 401/403/1008.

---

## Criterios de aceptacion

```gherkin
Feature: Infraestructura de frontend del modo en vivo (US-6.3.4)

  Scenario: El cliente API llama a los endpoints con JWT y mapea a camelCase
    Given una sesión guardada con token
    When se invoca cualquier función de sesion-en-vivo-api
    Then la request lleva el Authorization y la respuesta llega en camelCase

  Scenario: El canal recibe y tipa los mensajes
    Given un canal conectado a una sesión
    When llega un mensaje pregunta_cerrada
    Then el callback lo recibe tipado y en camelCase

  Scenario: El canal se reconecta y pide re-sincronizar
    Given un canal conectado que se cae
    When se restablece la conexión
    Then dispara onReconectado y el estado vuelve a conectado

  Scenario: El backoff es exponencial con tope
    Given una conexión que falla repetidamente
    When se reintenta
    Then los intervalos son 1, 2, 4, 8 y 10 segundos como máximo

  Scenario: Token inválido corta la conexión
    Given un canal con un token vencido
    When el servidor cierra con 1008
    Then no reintenta, limpia la sesión y navega a /login

  Scenario: Un mensaje desconocido no rompe
    Given un canal conectado
    When llega un mensaje con un tipo que el cliente no conoce
    Then se ignora y los siguientes se procesan

  Scenario: El cleanup cierra el socket
    Given un componente que usa el hook
    When se desmonta
    Then el socket queda cerrado y no reintenta

  Scenario: Las rutas están protegidas por rol
    Given un Estudiante
    When abre la ruta de proyección del Docente
    Then RequireRole lo rechaza

  Scenario: La proyección no usa el layout con menú
    Given la ruta de proyección
    When se renderiza
    Then usa StageLayout y no muestra el menú de navegación
```

---

## Impacto arquitectonico

- [ ] No — cliente y rutas sobre lo existente; el canal es nuevo pero acotado a un módulo de `lib/`.

**Capa(s) afectadas:**
- [ ] Entities / Use Cases / Interface Adapters / Frameworks — sin cambios de `src/`
- [x] Frontend

**Calidad (frontend):** `oxlint` 0 errores, `tsc -b` 0 errores (no `tsc --noEmit`: el `tsconfig.json` raíz usa `references`, lección de `US-ADJ-23`), cobertura ≥ 80% (`vitest.config` ya la exige). Tests con un `WebSocket` falso inyectable (jsdom no trae uno funcional).

---

## Fuente de verdad UX

- `docs/design/ux/wireframes-actividad-evaluativa-en-vivo.md` §1 (identidad visual, tokens `--stage-*`, colores de opción) y §1.1 (legibilidad en proyección).
- `docs/design/ux/prototipos/actividad-evaluativa-en-vivo.html` (paleta `--stage-bg #0f1b24`, `--stage-fg`, `--stage-accent`, `--stage-primary`; `.color-a/b/c/d`).
- H8 de `US-6.3.0` (indicador de conexión).

---

## Artefactos a modificar

| Artefacto | Cambio |
|---|---|
| `frontend/src/lib/sesion-en-vivo-api.ts` (+ `.test.ts`) | Cliente API (nuevo) |
| `frontend/src/lib/canal-sesion-en-vivo.ts`, `use-canal-sesion-en-vivo.ts` (+ tests) | Canal y hook (nuevos) |
| `frontend/src/layouts/StageLayout.tsx` | Layout de proyección (nuevo) |
| `frontend/src/index.css` | Tokens `--stage-*` y colores de opción |
| `frontend/src/router.tsx`, `frontend/src/router.test.tsx` | 4 rutas nuevas protegidas |
| `frontend/src/pages/actividad-evaluativa/…` | Placeholders temporales |

---

## Referencias

- Precedentes: `docs/specs/inc2/US-2.1.8.md`, `docs/specs/inc3/US-3.4.1.md`
- Lecciones: `US-ADJ-20` (StrictMode), `US-ADJ-23` (`tsc -b`)
- Backend: `docs/specs/inc6/US-6.1.1.md` (canal), `US-6.2.x`, `US-6.3.1` a `US-6.3.3`
- Bloquea a: `US-6.3.5` a `US-6.3.9`

---

*Basado en template IEDD v2.0 — adaptado a capas `entities/use_cases/interface_adapters/frameworks` (`CLAUDE.md`).*
