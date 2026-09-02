# Plan de Implementación: US-3.4.1 - Infraestructura de frontend de Actividad Evaluativa

**Patrón:** React 19 + TypeScript + Vite (sin Clean Architecture — no aplica a frontend)
**Producto:** actividad_evaluativa (frontend)
**Estado:** ✅ COMPLETADO
**Fecha completado:** 2026-08-30

## Métricas de Tiempo

| Fase | Tiempo real |
|------|-------------|
| 0 — Análisis de spec | 97s |
| 1 — Escenarios BDD | 26s |
| 2 — Plan de implementación | 87s |
| 3 — Implementación | 76s |
| 4 — Tests unitarios | 46s |
| 5 — Tests de integración | 65s |
| 6 — Validación BDD | 7s |
| 7 — Quality Gates | 150s |
| **Total (fases 0-7)** | **~9.2 min** |

> Sin comparación contra estimación humana (PRIN-001) — el tracking registra tiempo real de
> ejecución del agente, no tiempo humano equivalente.

## Lecciones Aprendidas

- ✅ Sin gap de backend en esta US (a diferencia de `US-2.1.8`) — los 9 endpoints consumidos
  por `US-3.4.2` a `US-3.4.7` ya existían tal cual, verificado leyendo directamente los 3
  routers (`actividades_router.py`/`evaluaciones_router.py`/`revision_router.py`) antes de
  escribir el cliente API.
- ✅ Mapeo explícito snake_case↔camelCase en `actividad-evaluativa-api.ts` (mismo criterio que
  `banco-preguntas-api.ts`) mantiene el frontend con convenciones TS idiomáticas.
- ✅ `Rol` en `session.ts` ya incluía `"estudiante"` desde su definición original — primer uso
  real en `RequireRole`, sin cambios de tipo necesarios.

## Alcance

Sin gap de backend en esta US (a diferencia de `US-2.1.8`): los 9 endpoints consumidos por
`US-3.4.2` a `US-3.4.7` ya existen tal cual en `actividades_router.py`/`evaluaciones_router.py`/
`revision_router.py` (Iteraciones 1-3). El gap de backend real (falta de `GET` de listado/
detalle) está fuera del alcance de esta US — cada US de pantalla que lo necesite lo resuelve en
su propio alcance (ya documentado en `inc3-candidatas.md` y en `US-3.4.1-context.md`).

## Componentes a Implementar

### 1. Cliente API del dominio
- [x] `frontend/src/lib/actividad-evaluativa-api.ts`
  - Funciones tipadas que envuelven `apiFetch` (reutilizan JWT/401/403 de `api-client.ts`, sin
    duplicar esa lógica), tipos de request/response reflejando
    `src/actividad_evaluativa/frameworks/api/schemas.py` (mapeo snake_case↔camelCase, mismo
    criterio que `banco-preguntas-api.ts`):
    - `crearActividad(body)` → `POST /actividades` (US-3.4.3)
    - `modificarPeriodoDisponibilidad(actividadId, nuevaFechaCierre)` → `PATCH /actividades/{id}/periodo` (US-3.4.4)
    - `cerrarActividad(actividadId)` → `POST /actividades/{id}/cerrar` (US-3.4.4)
    - `iniciarEvaluacion(actividadId)` → `POST /evaluaciones` (US-3.4.6)
    - `registrarRespuesta(evaluacionId, preguntaId, contenido)` → `POST /evaluaciones/{id}/respuestas` (US-3.4.6)
    - `suspenderEvaluacion(evaluacionId)` → `POST /evaluaciones/{id}/suspender` (US-3.4.6)
    - `reanudarEvaluacion(evaluacionId)` → `POST /evaluaciones/{id}/reanudar` (US-3.4.6)
    - `finalizarEvaluacion(evaluacionId)` → `POST /evaluaciones/{id}/finalizar` (US-3.4.7)
    - `obtenerRevision(evaluacionId)` → `GET /evaluaciones/{id}/revision` (US-3.4.7)
  - `contenido`/`contenidoPropio`/`contenidoCorrecto` tipados como `Record<string, unknown>`
    (mismo `dict[str, Any]` sin estructura fija del schema Pydantic — la forma concreta depende
    del tipo de pregunta, ya resuelta en Banco de Preguntas, no se re-valida acá)

### 2. Placeholder de pantalla
- [x] `frontend/src/pages/_placeholders.tsx`
  - Agregar `ActividadEvaluativaPlaceholder` (mismo criterio que `BancoPreguntasPlaceholder`,
    `US-2.1.8`) — destino temporal de todas las rutas nuevas hasta que `US-3.4.2` a `US-3.4.7`
    las reemplacen

### 3. Routing
- [x] `frontend/src/router.tsx`
  - Rutas nuevas dentro de `AppLayout`, cada bloque envuelto en el `RequireRole` de su rol
    (`docente` ya usado desde `US-2.1.9`; `estudiante` es primer uso):
    - `/actividad-evaluativa/materias` (US-3.4.2)
    - `/actividad-evaluativa/materias/:materiaId/actividades` (US-3.4.2)
    - `/actividad-evaluativa/materias/:materiaId/actividades/nueva` (US-3.4.3)
    - `/actividad-evaluativa/actividades/:actividadId` (US-3.4.4 — detalle)
    - `/actividad-evaluativa/actividades/:actividadId/extender-plazo` (US-3.4.4)
    - `/actividad-evaluativa/actividades/:actividadId/cerrar` (US-3.4.4)
    - `/mis-actividades/materias` (US-3.4.5, rol `estudiante`)
    - `/mis-actividades/materias/:materiaId/actividades` (US-3.4.5, rol `estudiante`)
    - `/mis-actividades/actividades/:actividadId/rendir` (US-3.4.6, rol `estudiante`)
    - `/mis-actividades/evaluaciones/:evaluacionId/revision` (US-3.4.7, rol `estudiante`)
  - Los estados "fuera de período" (`#est-fuera-periodo`) y "evaluación suspendida"
    (`#est-suspendida`) del wireframe se resuelven como estados de render dentro de
    `/mis-actividades/.../rendir` (o del listado), no como rutas propias — a confirmar/ajustar
    en la spec de `US-3.4.5`/`US-3.4.6` si el wireframe exige URL distinta.

### 4. Integración
- [x] Ninguna dependencia nueva — reutiliza `apiFetch`/`ApiError` (`api-client.ts`, `US-1.1.6`)
  y `RequireRole` (`US-1.1.9`) sin cambios. `Rol` ya incluye `"estudiante"` en `session.ts`.

**Estado:** 4/4 tareas completadas
