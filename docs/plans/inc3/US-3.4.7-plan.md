# Plan de Implementación: US-3.4.7 - Estudiante finaliza su evaluación y ve la revisión completa

**Patrón:** Clean Architecture (BC-first: entities → use_cases → interface_adapters → frameworks)
**Producto:** cognion (BC Actividad Evaluativa)
**Estado:** ✅ COMPLETADO
**Fecha completado:** 2026-08-31

## Métricas de Tiempo (tracker_cli.py)

| Fase | Tiempo real |
|------|-------------|
| 0 — Validación de Contexto | 34s |
| 1 — Escenarios BDD | 21s |
| 2 — Plan de Implementación | 136s |
| 3 — Implementación (6 tareas) | 250s |
| 4 — Tests Unitarios | 113s |
| 5 — Tests de Integración | 157s |
| 6 — Validación BDD | 186s |
| 7 — Quality Gates | 557s |
| **Total hasta Fase 7** | **~25 min** |

## Lecciones Aprendidas

- 💡 El gap del texto de opciones en la revisión (detectado en Fase 2) se resolvió extendiendo
  un solo campo (`opciones`) reutilizado en toda la cadena entities → use_case → schema →
  router, sin tocar la lógica de negocio existente — bajo costo por seguir el mismo shape ya
  usado en `ContenidoPregunta`.
- 💡 `codeguard` reportó 12 "errors" en la primera corrida por `vulture`/`codespell` no
  encontrados en `PATH` (venv no activado) — mismo problema ya documentado en `US-3.4.6`;
  anteponer `.venv/bin` al `PATH` antes de correr `codeguard` evita el falso resultado limpio.
- ✅ El botón "Confirmar y finalizar" reutilizando el flujo de la última pregunta (sin agregar
  una acción de UI nueva no contemplada en el prototipo) mantuvo el wireframe como fuente de
  verdad sin necesitar un nuevo ciclo de aprobación UX.

## Gap detectado en Fase 2 (decisión de Víctor)

`GET /evaluaciones/{id}/revision` (`US-3.2.3`) devuelve, para preguntas de opción múltiple, el
contenido de la respuesta como `{opcion_indice: N}` — sin el texto de la opción. El prototipo
aprobado (`#est-revision`) muestra texto real ("Tu respuesta: Herencia múltiple obligatoria").
Decisión: extender el backend en esta misma US para incluir el texto de las opciones, mismo
criterio que gaps previos resueltos dentro de la propia US (`US-2.1.9`, `US-2.2.8`, `US-ADJ-10`).

## Componentes a Implementar

### 1. Backend — extensión de `DetalleCorreccionPregunta` con opciones

- [x] `src/actividad_evaluativa/entities/ports/pregunta_consulta_port.py`
  - `DetalleCorreccionPregunta` gana el campo `opciones: list[str] | None` (mismo criterio que
    `ContenidoPregunta.opciones` — `None` para Verdadero/Falso, lista de textos en el orden
    original para Opción Múltiple)
- [x] `src/actividad_evaluativa/frameworks/adapters/pregunta_consulta_port_in_process.py`
  - `obtener_detalle_correccion` puebla `opciones` reutilizando la misma rama
    `isinstance(pregunta, PreguntaPlantillaOpcionMultiple)` que ya arma `contenido_correcto`
- [x] `src/actividad_evaluativa/entities/revision_evaluacion.py`
  - `DetallePreguntaRevision` gana el campo `opciones: list[str] | None`
- [x] `src/actividad_evaluativa/use_cases/obtener_revision_evaluacion.py`
  - `_detalle_de` puebla `opciones` desde `detalle_correccion.opciones`
- [x] `src/actividad_evaluativa/frameworks/api/schemas.py`
  - `DetallePreguntaRevisionResponse` gana el campo `opciones: list[str] | None`
- [x] `src/actividad_evaluativa/frameworks/api/revision_router.py`
  - `_a_response` mapea el campo nuevo

### 2. Frontend — cliente API (`actividad-evaluativa-api.ts`)

- [x] `DetallePreguntaRevisionResponse` (interfaz TS) gana `opciones: string[] | null`
- [x] `mapearRevision` mapea `opciones` (snake_case `opciones` → camelCase igual, sin cambio de
      nombre)

### 3. Frontend — pantalla de revisión (`RevisionEvaluacion.tsx`)

- [x] `frontend/src/pages/RevisionEvaluacion.tsx` — nueva
  - Lee `evaluacionId` de la URL (`/mis-actividades/evaluaciones/:evaluacionId/revision`)
  - Llama `obtenerRevision(evaluacionId)` al montar
  - Resumen: barra con correctas/incorrectas/total (`§3.5` del wireframe, `summary-bar` del
    prototipo)
  - Detalle por pregunta, ordenado por `orden`: enunciado, `Badge` correcta/incorrecta, "Tu
    respuesta: {texto}" (resuelto desde `contenidoPropio` + `opciones`, o "Verdadero"/"Falso"
    si `opciones` es `null`; "Sin responder" si `respondida` es `false`), y — solo si
    `esCorrecta` es `false` — "Respuesta correcta: {texto}" resuelto igual desde
    `contenidoCorrecto`
  - Breadcrumb consistente con `MisActividades.tsx` (Mis materias › — sin nombre de materia
    disponible en la respuesta de revisión, usar el mismo patrón simplificado que
    `RendirEvaluacion.tsx`, sin breadcrumb completo si no hay dato de materia)

### 4. Frontend — botón "Finalizar" en `RendirEvaluacion.tsx`

- [x] `frontend/src/pages/RendirEvaluacion.tsx`
  - Cuando `indiceActual` es la última pregunta, el botón cambia su texto de "Confirmar y
    siguiente" a "Confirmar y finalizar"
  - Al confirmar la última pregunta: además de `registrarRespuesta`, llama
    `finalizarEvaluacion(evaluacion.id)` y navega a
    `/mis-actividades/evaluaciones/${evaluacion.id}/revision`
  - Nota de diseño: el prototipo no muestra un botón "Finalizar" separado — el criterio de
    aceptación de la spec ("elige finalizar") se cubre reusando el flujo de confirmación de la
    última pregunta, sin agregar una acción nueva a la UI que el wireframe no contempla

### 5. Integración — ruta

- [x] `frontend/src/router.tsx` — reemplazar `ActividadEvaluativaPlaceholder` por
      `RevisionEvaluacion` en la ruta `/mis-actividades/evaluaciones/:evaluacionId/revision`
      (ya protegida con `RequireRole rol="estudiante"` desde `US-3.4.1`)

**Estado:** 6/6 tareas completadas
