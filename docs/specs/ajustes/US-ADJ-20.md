# US-ADJ-20: `AbortController` en los fetch de `useEffect`/submit del frontend

**Estado**: `Especificada`
**Iteracion / Sprint**: `Incremento 3-ADJ — Adecuación Técnica`
**Tipo**: `fix técnico frontend` (robustez — sin cambio de comportamiento observable para el
usuario)
**Agregado principal afectado**: ninguno — no toca dominio
**Bounded Context**: transversal (las 4 áreas de frontend: Identidad, Cuentas, Banco de
Preguntas, Actividad Evaluativa)
**Origen**: investigación de esta sesión sobre un `unhandled rejection` intermitente en CI
(`ECONNREFUSED`/`TypeError: Cannot read properties of undefined (reading 'status')`) que
Vitest 4.1.11 empezó a exponer como fallo duro — confirmado como una condición de carrera
pre-existente en `develop`, no introducida por ningún PR de Dependabot.

---

## Descripcion (lenguaje de negocio)

Como **desarrollador del proyecto**,
quiero **que los `fetch` disparados desde `useEffect` (y desde los `handleSubmit` async) se
cancelen realmente al desmontar el componente, en vez de solo ignorar su resultado**
para **eliminar una condición de carrera real del frontend que hoy se manifiesta como fallos
intermitentes en la suite de tests (y, en producción, como una posible actualización de estado
o navegación fantasma si el usuario navega rápido entre pantallas)**.

---

## Contexto del dominio

### Problema

`frontend/src/pages/` tiene 21 componentes que siguen el mismo patrón para sus `fetch` de
`useEffect`:

```ts
useEffect(() => {
  let cancelado = false
  algunaLlamadaApi().then((datos) => {
    if (!cancelado) setEstado(datos)
  })
  return () => { cancelado = true }
}, [dep])
```

El guard `cancelado` evita el `setState` posterior al desmontaje (silencia el warning clásico de
React), pero **no cancela el `fetch` en sí** — la promesa de red sigue en vuelo después de que
el componente se desmontó, y nadie maneja su eventual rechazo (`.then` sin `.catch`).

En producción esto es inofensivo la mayoría de las veces (la promesa se resuelve y su resultado
simplemente se descarta). En tests es donde se vuelve visible: cada archivo de test reemplaza
`global.fetch` con un `vi.fn()` nuevo en su propio `beforeEach` y lo saca con
`vi.unstubAllGlobals()` en `afterEach`. Si la promesa de un componente ya desmontado (de un test
anterior, o de una interacción — como un submit — que no llegó a completarse antes de que el
test terminara) se resuelve *después* de que el siguiente test ya instaló su propio mock vacío,
`fetch()` devuelve `undefined` sincrónicamente (comportamiento default de un `vi.fn()` sin
`mockResolvedValueOnce` encolado) y el código explota en `apiFetch`
(`frontend/src/lib/api-client.ts:52`, `response.status` sobre `undefined`) — o, en CI, cae al
`fetch` real de Node contra un backend que no existe (`ECONNREFUSED`).

Confirmado en esta sesión: el mismo patrón de fallo (`TypeError: fetch failed` /
`ECONNREFUSED 127.0.0.1:8000`, originado en distintos archivos de test — `ActividadDetalle`,
`NuevaPreguntaOpcionMultiple`) apareció en corridas de CI de PRs sin ninguna relación entre sí
(un bump de `@tailwindcss/vite`, un bump de `vitest`), y desapareció al reintentar el mismo job
sin cambiar una sola línea de código — es una condición de carrera de timing, no un bug
determinístico introducido por ningún cambio puntual.

Es además el peor caso en `handleSubmit`: los `handleSubmit` async de formularios de creación
(ej. `NuevaPreguntaOpcionMultiple.tsx:87-111`) llaman a su función de API **sin ningún guard de
desmontaje** — ni `cancelado` ni `AbortController`. Si el usuario navega away mientras el submit
está en vuelo (o un test lo desmonta antes de que la promesa resuelva), no hay ningún mecanismo
que lo cubra.

### Alcance del fix

Reemplazar el patrón `cancelado` por `AbortController` en los `useEffect` con fetch, y agregar
un guard equivalente a los `handleSubmit` async que hoy no tienen ninguno. Como `apiFetch`
(`frontend/src/lib/api-client.ts:38`) ya hace `fetch(url, { ...options, ... })` y
`ApiFetchOptions extends Omit<RequestInit, "body">`, **`signal` ya se propaga sin tocar
`api-client.ts`** — solo hace falta:

1. Agregar un parámetro `signal?: AbortSignal` a cada función exportada de las 4 APIs tipadas
   (`frontend/src/lib/actividad-evaluativa-api.ts`, `banco-preguntas-api.ts`, `cuentas-api.ts`,
   `identidad-estudiante-api.ts` — 32 llamadas a `apiFetch` en total) que lo reenvíe como
   `options.signal`.
2. En cada uno de los 21 componentes de `frontend/src/pages/` con el patrón `cancelado`:
   reemplazarlo por `const controller = new AbortController()`, pasar `controller.signal` a la
   llamada de API, y `return () => controller.abort()` en el cleanup del efecto. Agregar
   `.catch((err) => { if (err.name !== "AbortError") throw err })` (o equivalente) para no dejar
   la promesa sin manejar cuando se aborta — un abort **debe** producir un rechazo silencioso,
   no un unhandled rejection nuevo.
3. En los `handleSubmit` async que llaman a la API sin ningún guard (`NuevaPreguntaOpcionMultiple.tsx`
   y cualquier otro formulario de creación/edición con el mismo problema — relevar durante la
   implementación), agregar el mismo mecanismo: `AbortController` creado en el efecto de montaje
   del componente (o uno propio para el submit), abortado en el cleanup.

**Fuera de alcance de esta US:**
- No se toca `api-client.ts` (ya soporta `signal` transitivamente).
- No se reordena `frontend/src/pages/` (eso es `US-ADJ-14`, independiente).
- No se agregan tests nuevos específicos para la cancelación (verificar que la suite existente
  sigue en verde y que el `unhandled rejection` deja de aparecer es suficiente evidencia).
- No hay cambio de UX ni de contrato HTTP — no aplica el gate de diseño UX
  (`docs/design/ux/`).

---

## Especificacion del comportamiento

### Precondicion

- 21 componentes en `frontend/src/pages/` usan el guard `cancelado` (sin `AbortController`) en
  sus `useEffect` con fetch.
- Al menos `NuevaPreguntaOpcionMultiple.tsx` tiene un `handleSubmit` async sin ningún guard de
  desmontaje.
- La suite de frontend (`npx vitest run`) es intermitentemente inestable por esta causa —
  confirmado en corridas de CI de PRs no relacionados.

### Postcondicion

- Los 21 componentes cancelan su(s) `fetch` de `useEffect` vía `AbortController.abort()` al
  desmontarse, en vez de solo ignorar el resultado.
- `handleSubmit` (y cualquier otro submit async con el mismo problema, relevado durante la
  implementación) también aborta su fetch en vuelo si el componente se desmonta antes de que
  resuelva.
- Ningún abort deja una promesa sin manejar (`AbortError` se captura explícitamente en cada
  sitio, no se propaga como `unhandled rejection`).
- `npx vitest run` corrido repetidamente (mínimo 10 veces seguidas, o con `--reporter=verbose`
  en paralelo con otro archivo sospechoso como en la investigación previa) no vuelve a mostrar
  el `unhandled rejection`/`ECONNREFUSED` observado.
- El comportamiento observable de cada pantalla no cambia — mismos datos mostrados, mismas
  validaciones, mismas navegaciones tras un submit exitoso.

### Invariantes

Ninguna — no hay cambio de dominio, es un fix de robustez técnica en la capa de presentación.

---

## Criterios de aceptacion

```gherkin
Feature: Cancelación real de fetch en desmontaje (US-ADJ-20)

  Scenario: Un componente desmontado no deja un fetch pendiente sin manejar
    Given un componente de frontend/src/pages/ con un useEffect que dispara fetch
    When el componente se desmonta antes de que el fetch resuelva
    Then el AbortController del efecto se aborta
    And el rechazo por AbortError se captura sin propagarse como unhandled rejection

  Scenario: Un submit en vuelo no rompe si el componente se desmonta
    Given un formulario de creación/edición con handleSubmit async
    When el usuario navega away (o el test desmonta el componente) mientras el submit está en vuelo
    Then el fetch del submit se aborta
    And no se produce ningún unhandled rejection

  Scenario: La suite de tests deja de ser intermitente por esta causa
    Given la suite completa de frontend (npx vitest run)
    When se corre repetidamente (mínimo 10 corridas seguidas)
    Then ninguna corrida muestra el unhandled rejection ECONNREFUSED / "Cannot read properties of undefined (reading 'status')"
```

---

## Impacto arquitectonico

**¿Esta US requiere una decision arquitectonica?**
- [x] No — fix de robustez dentro de un patrón ya establecido (mismo guard de desmontaje,
  reemplazando el mecanismo, sin cambiar la forma en que los componentes consumen las APIs
  tipadas).

**Capa(s) afectadas:**
- [x] Frontend — `frontend/src/pages/*.tsx` (21 componentes), `frontend/src/lib/*-api.ts` (4
  archivos, 32 sitios de `apiFetch`)
- [ ] Backend — sin cambios

---

## Artefactos a modificar

| Artefacto | Cambio |
|---|---|
| `frontend/src/lib/actividad-evaluativa-api.ts`, `banco-preguntas-api.ts`, `cuentas-api.ts`, `identidad-estudiante-api.ts` | Cada función exportada que llama `apiFetch` acepta `signal?: AbortSignal` opcional y lo reenvía |
| `frontend/src/pages/*.tsx` (21 archivos con el patrón `cancelado`, ver lista en la investigación de esta sesión) | `useEffect` migrado de `cancelado` a `AbortController` |
| `frontend/src/pages/NuevaPreguntaOpcionMultiple.tsx` (y cualquier otro `handleSubmit` sin guard, a relevar) | Agregar guard de desmontaje al submit async |

---

## Referencias

- Relacionada con: la investigación de esta sesión sobre el flake de CI en PRs de Dependabot
  (#126, #129) — reporte completo en la conversación, no persistido como documento aparte.
- Detectada durante: triage de Pull Requests de Dependabot, 2026-09-02.

---

*Basado en template IEDD v2.0 — adaptado a capas `entities/use_cases/interface_adapters/frameworks` (`CLAUDE.md`).*
