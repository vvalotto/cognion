# Plan de Implementación: US-ADJ-20 - AbortController en fetch de useEffect/submit del frontend

**Patrón:** Frontend React + TS (transversal, no aplica Clean Architecture por capas de BC)
**Producto:** cognion (frontend)

## Componentes a Implementar

### 1. Capa de API tipada — agregar `signal?: AbortSignal`

`api-client.ts` **no se toca** — `ApiFetchOptions extends Omit<RequestInit, "body">` ya
propaga `signal` al `fetch` interno sin cambios.

- [ ] `frontend/src/lib/actividad-evaluativa-api.ts` (15 llamadas a `apiFetch`)
  - Cada función exportada acepta `signal?: AbortSignal` como último parámetro opcional y lo
    reenvía como `{ signal }` en las options de `apiFetch`
- [ ] `frontend/src/lib/banco-preguntas-api.ts` (9 llamadas)
  - Ídem
- [ ] `frontend/src/lib/cuentas-api.ts` (6 llamadas)
  - Ídem
- [ ] `frontend/src/lib/identidad-estudiante-api.ts` (2 llamadas)
  - Ídem

### 2. Componentes con `useEffect` + fetch — migrar `cancelado` → `AbortController`

Reemplazar el guard `let cancelado = false` por `const controller = new AbortController()`,
pasar `controller.signal` a la(s) llamada(s) de API del efecto, `return () => controller.abort()`
en el cleanup, y agregar `.catch((err) => { if (err.name !== "AbortError") throw err })` (o un
`try/catch` async equivalente) para que el abort no deje un `unhandled rejection`.

- [ ] `frontend/src/pages/ActividadDetalle.tsx`
- [ ] `frontend/src/pages/Actividades.tsx`
- [ ] `frontend/src/pages/Banco.tsx`
- [ ] `frontend/src/pages/CerrarActividad.tsx`
- [ ] `frontend/src/pages/CuentaDetalle.tsx`
- [ ] `frontend/src/pages/Cuentas.tsx`
- [ ] `frontend/src/pages/EditarPregunta.tsx`
- [ ] `frontend/src/pages/EditarTituloActividad.tsx`
- [ ] `frontend/src/pages/EliminarPregunta.tsx`
- [ ] `frontend/src/pages/EvaluacionSuspendida.tsx`
- [ ] `frontend/src/pages/ExtenderPlazo.tsx`
- [ ] `frontend/src/pages/Materias.tsx`
- [ ] `frontend/src/pages/MateriasActividades.tsx`
- [ ] `frontend/src/pages/MisActividades.tsx`
- [ ] `frontend/src/pages/MisMaterias.tsx`
- [ ] `frontend/src/pages/NuevaActividad.tsx`
- [ ] `frontend/src/pages/NuevaPreguntaOpcionMultiple.tsx`
- [ ] `frontend/src/pages/NuevaPreguntaTipo.tsx`
- [ ] `frontend/src/pages/NuevaPreguntaVerdaderoFalso.tsx`
- [ ] `frontend/src/pages/RendirEvaluacion.tsx`
- [ ] `frontend/src/pages/ResetearPassword.tsx`
- [ ] `frontend/src/pages/RevisionEvaluacion.tsx`

### 3. Componentes con `handleSubmit` async sin guard de desmontaje

Agregar un `AbortController` de ciclo de vida del componente (creado en un `useEffect` sin
dependencias al montar, abortado en su cleanup) y pasar su `signal` a la llamada de API dentro
de `handleSubmit`. En los componentes que ya están en el grupo 2, reutilizar el mismo
`AbortController` del efecto principal si el ciclo de vida coincide; si no, agregar uno propio.

- [ ] `frontend/src/pages/AltaDocente.tsx`
- [ ] `frontend/src/pages/CambiarPassword.tsx`
- [ ] `frontend/src/pages/EditarPregunta.tsx` *(ya en grupo 2 — reutilizar controller)*
- [ ] `frontend/src/pages/EditarTituloActividad.tsx` *(ya en grupo 2 — reutilizar controller)*
- [ ] `frontend/src/pages/ExtenderPlazo.tsx` *(ya en grupo 2 — reutilizar controller)*
- [ ] `frontend/src/pages/Login.tsx`
- [ ] `frontend/src/pages/NuevaActividad.tsx` *(ya en grupo 2 — reutilizar controller)*
- [ ] `frontend/src/pages/NuevaMateria.tsx`
- [ ] `frontend/src/pages/NuevaPreguntaOpcionMultiple.tsx` *(ya en grupo 2 — reutilizar controller)*
- [ ] `frontend/src/pages/NuevaPreguntaVerdaderoFalso.tsx` *(ya en grupo 2 — reutilizar controller)*
- [ ] `frontend/src/pages/Registro.tsx`
- [ ] `frontend/src/pages/ResetearPassword.tsx` *(ya en grupo 2 — reutilizar controller)*

### 4. Verificación

- [ ] `npx oxlint` en verde
- [ ] `npx tsc -b --noEmit` en verde
- [ ] `npx vitest run` en verde, corrido repetidamente (mínimo 5 veces seguidas) sin que
  reaparezca el `unhandled rejection` / `ECONNREFUSED`

**Estado:** 0/31 archivos modificados (4 de API + 27 de páginas, con solapamiento entre grupos
2 y 3 ya contabilizado una sola vez por archivo)

---

## Notas de implementación

- **Orden bottom-up:** grupo 1 (API) primero — grupo 2 y 3 dependen de que `signal` ya exista
  como parámetro en las funciones que consumen.
- **Sin cambio de contrato ni de UX:** ningún schema Pydantic, ninguna URL, ningún JSON de
  request/response cambia. No aplica el gate de diseño UX (`docs/design/ux/`).
- **Fuera de alcance:** no se reordena `frontend/src/pages/` (`US-ADJ-14`, independiente); no
  se agregan tests nuevos específicos de cancelación — la suite existente corriendo estable
  repetidamente es la evidencia de cierre.
