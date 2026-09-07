# Plan de Implementación: US-ADJ-24 - Administrador crea una Comisión

**Patrón:** Clean Architecture BC-First (sin capas de dominio en esta US — 100% `frontend/`)
**Producto:** cognion (BC Identidad)
**Estado:** ✅ COMPLETADO
**Fecha completado:** 2026-09-07

## Métricas de Tiempo

Tracking real (`tracker_cli.py status`), ~16 min efectivos entre Fase 0 y Fase 8. Sin
comparación contra estimación humana (PRIN-001 — el tracking mide tiempo real de agente, no
tiempo humano equivalente).

## Lecciones Aprendidas

- ✅ `administrador_id` no tenía forma de resolverse en el frontend (`Session` solo persistía
  `token`/`rol`) — decodificar el claim `sub` del JWT client-side (sin librería nueva, sin
  endpoint `GET /usuarios/me`) fue la solución más simple, consistente con "sin cambios de
  backend" ya decidido en la spec.
- ✅ El patrón de `AbortController` creado en `useEffect` (`US-ADJ-20`) se reutilizó tal cual —
  ninguna sorpresa de `StrictMode` en dev.

## Componentes a Implementar

### 1. Helper de sesión — decodificar `sub` del JWT
- [x] `frontend/src/lib/session.ts`
  - `obtenerUsuarioId(): string | null` — decodifica el payload (segundo segmento) del JWT
    almacenado en `Session.token` (base64url → JSON), devuelve el claim `sub`. `null` si no
    hay sesión o el token es inválido (no debería ocurrir en uso normal, pero evita un throw
    no controlado).

### 2. Cliente API — Comisiones
- [x] `frontend/src/lib/identidad-comisiones-api.ts`
  - `crearComision(materiaId: string, horario: string, signal?: AbortSignal): Promise<{ id: string }>`
    — resuelve `administrador_id` con `obtenerUsuarioId()`, `POST /comisiones` con
    `{ materia_id, horario, administrador_id }`, devuelve `{ id }` del `ComisionResponse`.

### 3. Pantalla — Nueva Comisión
- [x] `frontend/src/pages/identidad/NuevaComision.tsx`
  - Formulario: selector de Materia (`listarMaterias()`, ya existente en
    `banco-preguntas-api.ts`) preseleccionado si la URL trae `?materiaId=`
    (`useSearchParams`); campo Horario (texto libre, `required`).
  - Submit → `crearComision(...)` → `navigate(`/comisiones/${id}`)`.
  - Cancelar → `navigate` de vuelta a `/comisiones` (con `materiaId` si había preselección,
    para no perder el filtro).
  - Mismo patrón de `AbortController` creado en `useEffect` que `NuevaMateria.tsx`
    (`US-ADJ-20`) — evita el bug de `StrictMode` ya documentado.

### 4. Integración
- [x] `frontend/src/pages/identidad/Comisiones.tsx` — el botón "+ Nueva Comisión" navega a
  `/comisiones/nueva?materiaId=${materiaId}` en vez de `/comisiones/nueva`.
- [x] `frontend/src/router.tsx` — ruta `/comisiones/nueva` usa `NuevaComision` en vez de
  `ComisionPlaceholder` (import nuevo, elimina el uso de `ComisionPlaceholder` para esa ruta
  — `/comisiones/:comisionId` lo sigue usando, no se toca).

**Estado:** 4/4 tareas completadas
