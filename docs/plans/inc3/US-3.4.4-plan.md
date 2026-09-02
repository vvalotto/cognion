# Plan de Implementación: US-3.4.4 - Docente ve el detalle de una actividad, extiende el plazo y la cierra manualmente

**Patrón:** Clean Architecture BC-first
**Producto:** cognion (BC Actividad Evaluativa)
**Estado:** ✅ COMPLETADO
**Fecha completado:** 2026-08-30

## Métricas de Tiempo (real, tracker_cli)

| Fase | Real |
|------|------|
| Fase 0 — Validación de contexto | 39s |
| Fase 1 — BDD | 73s |
| Fase 2 — Plan | 319s |
| Fase 3 — Implementación (9 tareas) | 233s |
| Fase 4 — Tests unitarios | 172s |
| Fase 5 — Tests de integración | 116s |
| Fase 6 — Validación BDD | 190s |
| Fase 7 — Quality gates | 468s |
| **Total (Fases 0-7)** | **~27 min** |

> Nota PRIN-001: tiempos de ejecución del agente, no comparables a estimación humana en puntos.

## Lecciones aprendidas

- 💡 Antes de diseñar un tipo nuevo (`ActividadDetalle` propuesto por la spec), revisar el
  código ya existente del mismo BC — `ActividadResumen`/`ActividadResumenResponse` (`US-3.4.2`)
  ya cubrían todos los campos pedidos; evitó un tipo redundante y una capa extra de mapeo.
- ⚠️ Al escribir los step_defs BDD, generar el `nuevo cierre` en base a `datetime.now(UTC)` sin
  anclarlo a la `fecha_apertura` real de la actividad produjo un `PeriodoInvalido` en vez del
  `NoSePuedeAcortarConEvaluacionesActivas` esperado — corregido calculando el cierre relativo al
  período real creado en el step, no a una ventana fija independiente.

## Ajuste respecto de la spec (detectado en Fase 2)

La spec (`docs/specs/inc3/US-3.4.4.md`) propone un tipo nuevo `ActividadDetalle` que extiende
`ActividadResumen` con `cantidad_preguntas` e `intentos_permitidos`. Al revisar
`actividad_query_port.py` (`US-3.4.2`), **`ActividadResumen` ya tiene esos dos campos** —
se agregaron en `US-3.4.2` porque el listado también los necesita (tarjetas de `Actividades.tsx`).
`ActividadResumenResponse` (schema) también ya expone todo lo que pide el wireframe §2.3
(apertura, cierre, preguntas, intentos, conteos de evaluaciones activas/finalizadas).

**Decisión:** no crear `ActividadDetalle` ni un schema nuevo — `obtener()` devuelve
`ActividadResumen` (mismo tipo que `listar_por_materia()`), y el endpoint reusa
`ActividadResumenResponse`. Evita un tipo redundante sin perder ningún dato pedido por la spec
o el wireframe.

## Componentes a Implementar

### 1. Backend — Puerto y Use Case

- [x] `src/actividad_evaluativa/entities/ports/actividad_query_port.py`
  - Agrega `obtener(actividad_id: UUID) -> ActividadResumen | None` (abstracto) a `ActividadQueryPort`
- [x] `src/actividad_evaluativa/frameworks/adapters/actividad_query_repository.py`
  - Implementa `obtener()`: reconstruye el stream de `actividad_id`, filtra por tipo
    `ActividadEvaluativaPeriodoAbierto`; `None` si no existe. Reutiliza `_a_resumen` y
    `_contar_evaluaciones` ya existentes (evita duplicar la lógica de conteo)
- [x] `src/actividad_evaluativa/use_cases/obtener_actividad.py` (nuevo)
  - `ObtenerActividadUseCase.execute(actividad_id) -> ActividadResumen`
  - Lanza `ActividadNoExiste` si el puerto devuelve `None` (mismo patrón que `ObtenerCuentaUseCase`, `US-2.2.3`)

### 2. Backend — Controller y Router

- [x] `src/actividad_evaluativa/interface_adapters/controllers/actividades_query_controller.py`
  - Inyecta `ObtenerActividadUseCase` además de `ListarActividadesUseCase` (2 dependencias — lejos del umbral de CBO que ya generó CRITICAL con 3+)
  - Nuevo método `obtener_actividad(actividad_id) -> ActividadResumen`
- [x] `src/actividad_evaluativa/frameworks/api/actividades_router.py`
  - Nuevo `GET /{actividad_id}` → `response_model=ActividadResumenResponse` (reutilizado, sin schema nuevo), rol `docente`, 404 si `ActividadNoExiste`. `ActividadResumenResponse` gana `cerrada_manualmente`
- [x] `src/actividad_evaluativa/frameworks/dependencies.py`
  - `get_actividades_query_controller`: arma `ObtenerActividadUseCase(actividad_query)` y lo inyecta junto al existente

### 3. Frontend — Cliente API

- [x] `frontend/src/lib/actividad-evaluativa-api.ts`
  - `obtenerActividad(actividadId: string): Promise<ActividadResumenResponse>` — `GET /actividades/{id}`, reutiliza `mapearActividadResumen` ya existente. `ActividadResumenResponse` (TS) gana `cerradaManualmente`

### 4. Frontend — Pantallas (reemplazan los 3 placeholders de `US-3.4.1`)

- [x] `frontend/src/pages/ActividadDetalle.tsx` (nueva)
  - Trae la actividad con `obtenerActividad`, breadcrumb "Mis materias › {Materia} › Actividades › {Actividad}" (resuelve nombre de materia con `listarMaterias`, mismo patrón que `Actividades.tsx`)
  - Datos: apertura, cierre, cantidad de preguntas, intentos permitidos, evaluaciones activas, evaluaciones finalizadas, `Badge` de estado (reutiliza `ETIQUETA_ESTADO`/`VARIANTE_ESTADO` de `Actividades.tsx`, duplicado localmente — mismo criterio de duplicación mínima ya usado en otras pantallas del proyecto)
  - Acción "Extender plazo" — visible solo si `!cerradaManualmente`
  - Acción "Cerrar actividad ahora" (destructiva) — mismo criterio de visibilidad
- [x] `frontend/src/pages/ExtenderPlazo.tsx` (nueva)
  - Formulario: cierre actual (solo lectura) + nuevo cierre (`datetime-local`)
  - Validación de cliente: nuevo cierre no vacío (la validación de "no acortar con evaluaciones activas" es 100% server-side, según la spec — el cliente no la anticipa)
  - Éxito → navega de vuelta al detalle; error 422 (`NoSePuedeAcortarConEvaluacionesActivas`, `PeriodoInvalido`, `ActividadYaCerrada`) → inline, mismo patrón que `NuevaActividad.tsx` (`ApiError.status === 422`)
- [x] `frontend/src/pages/CerrarActividad.tsx` (nueva)
  - Confirmación destructiva, mismo patrón visual que `EliminarPregunta.tsx` (alerta + botón `destructive-solid` + Cancelar)
  - Éxito → navega de vuelta al detalle mostrando `Cerrada`

### 5. Integración

- [x] `frontend/src/router.tsx`
  - Reemplaza los 3 `ActividadEvaluativaPlaceholder` en `/actividad-evaluativa/actividades/:actividadId`, `/extender-plazo` y `/cerrar` por `ActividadDetalle`, `ExtenderPlazo`, `CerrarActividad` (rutas ya existen desde `US-3.4.1`, con `RequireRole rol="docente"`)

## Nota de diseño resuelta en Fase 3

Corrección sobre lo anticipado en Fase 2: `ActividadResumen` (el dataclass del puerto, entity)
**ya tenía** `cerrada_manualmente` desde `US-3.4.2` — no hacía falta agregarlo ahí. Lo que
faltaba era únicamente en el borde de la API: `ActividadResumenResponse` (schema Pydantic) y su
contraparte TypeScript en `actividad-evaluativa-api.ts` solo exponían `estado` derivado, sin el
campo puntual. Se agregó `cerrada_manualmente`/`cerradaManualmente` en ambos (schema + tipo TS +
mapeo), sin tocar el dominio.

**Estado:** 9/9 tareas completadas
