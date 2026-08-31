# Plan de Implementación: US-3.4.6 - Estudiante rinde su evaluación — responde, pausa y reanuda

**Patrón:** Clean Architecture BC-First (entities → use_cases → interface_adapters → frameworks)
**Producto:** cognion — BC Actividad Evaluativa
**Estado:** ✅ COMPLETADO
**Fecha completado:** 2026-08-31

## Métricas de Tiempo

| Fase | Tiempo real |
|------|-------------|
| 0 — Validación de Contexto | 32s |
| 1 — Escenarios BDD | 24s |
| 2 — Plan de Implementación | 3m 34s |
| 3 — Implementación (7 tareas) | 4m 31s |
| 4 — Tests Unitarios | 3m 19s |
| 5 — Tests de Integración | 3m 38s |
| 6 — Validación BDD | 2m 12s |
| 7 — Quality Gates | 9m 20s |
| **Total (Fases 0–7)** | **~27m 30s** |

## Lecciones Aprendidas

- ✅ Reusar el cliente API de frontend existente (`actividad-evaluativa-api.ts`, sin
  endpoints nuevos del lado UI) redujo la Fase 3 de frontend a solo 2 pantallas + rutas.
- ✅ Separar `PreguntaConsultaPort` como dependencia de FastAPI propia del router (en vez de
  sumarla al `EvaluacionesController`) evitó de entrada el patrón de CRITICAL de CBO que
  apareció repetidas veces en incrementos anteriores al agregar dependencias a controllers ya
  cargados.
- 💡 Primera US en correr `codeguard --analysis-type full` con vulture/codespell realmente
  instalados en el PATH del subproceso — reveló que el patrón "not installed" de corridas
  anteriores enmascaraba, no la ausencia de hallazgos, sino falsos positivos sistemáticos de
  vulture sobre métodos ABC/Pydantic/dataclass. Documentado como observación en
  `quality/reports/inc3/US-3.4.6-quality.json` y como sugerencia de tarea técnica futura
  (whitelist de vulture).

## Decisión de diseño (desvío menor respecto de la tabla "Artefactos a modificar" de la spec)

La spec asigna el poblado de `enunciado`/`opciones`/`preguntas_respondidas` a
`use_cases/iniciar_evaluacion.py`. Ese Use Case devuelve la entidad `Evaluacion` (dominio puro,
sin conocer texto de preguntas — mezclarlo violaría la regla de capas de `CLAUDE.md`). El punto
real donde hoy se construye `EvaluacionResponse` es `_a_response()` en
`frameworks/api/evaluaciones_router.py`, reusado por los 4 endpoints
(`iniciar`/`registrar_respuesta` no, pero `suspender`/`reanudar`/`finalizar` sí). Se enriquece
ahí, no en el Use Case, y se aplica a los 4 endpoints que devuelven `EvaluacionResponse` por
consistencia (mismo costo: una consulta más al puerto ya existente, sin impacto de performance
a esta escala).

`PreguntaConsultaPort` se inyecta como dependencia de FastAPI separada en el router (no como
6° dependencia del `EvaluacionesController`, que ya tiene 5 Use Cases inyectados — evita repetir
el patrón de CRITICAL de CBO ya visto en `US-2.1.2`/`US-2.1.5`/`US-2.1.6`/`US-3.1.3`/`US-3.2.1`).

## Componentes a Implementar

### 1. Backend — Puerto y adaptador (entities/frameworks)
- [x] `src/actividad_evaluativa/entities/ports/pregunta_consulta_port.py`
  - `ContenidoPregunta` (`dataclass frozen`): `texto: str`, `opciones: list[str] | None`
    (`None` para Verdadero/Falso, lista de textos — sin marcar cuál es correcta — para Opción
    Múltiple)
  - `obtener_contenido(pregunta_id) -> ContenidoPregunta` (método abstracto nuevo)
- [x] `src/actividad_evaluativa/frameworks/adapters/pregunta_consulta_port_in_process.py`
  - Implementa `obtener_contenido()`: reusa `_pregunta_repositorio.obtener_por_id()`
    (ya usado por `evaluar_correccion`/`obtener_detalle_correccion`), mismo criterio defensivo
    (`PreguntaNoAsignada` si `None`)

### 2. Backend — Schemas (frameworks/api)
- [x] `src/actividad_evaluativa/frameworks/api/schemas.py`
  - `PreguntaAsignadaResponse` += `enunciado: str`, `opciones: list[str] | None`
  - `EvaluacionResponse` += `preguntas_respondidas: list[UUID]` (ids únicos con `Respuesta`
    confirmada, derivado de `Evaluacion.respuestas`, sin duplicados si hubo reintentos)

### 3. Backend — Dependency injection y router
- [x] `src/actividad_evaluativa/frameworks/dependencies.py`
  - `get_pregunta_consulta_port(session: SessionDep) -> PreguntaConsultaPort` — nueva función,
    mismo patrón que las ya existentes (`PreguntaConsultaPortInProcess(session)`)
- [x] `src/actividad_evaluativa/frameworks/api/evaluaciones_router.py`
  - `_a_response()` pasa a `async`, recibe `pregunta_consulta: PreguntaConsultaPort`, arma
    `enunciado`/`opciones` por cada `PreguntaAsignada` y `preguntas_respondidas` desde
    `evaluacion.respuestas`
  - Los 4 endpoints que llaman `_a_response` (`iniciar_evaluacion`, `suspender_evaluacion`,
    `reanudar_evaluacion`, `finalizar_evaluacion`) agregan
    `Depends(get_pregunta_consulta_port)` y `await`

### 4. Frontend — Cliente API
- [x] `frontend/src/lib/actividad-evaluativa-api.ts`
  - `PreguntaAsignadaResponse` += `enunciado: string`, `opciones: string[] | null`
  - `EvaluacionResponse` += `preguntasRespondidas: string[]`
  - Mismo tratamiento en los tipos `*ApiResponse` (snake_case) y en `mapearEvaluacion()`

### 5. Frontend — Pantalla "Rendir evaluación" (`#est-rendir`)
- [x] `frontend/src/pages/RendirEvaluacion.tsx` (nueva)
  - Ruta: `/mis-actividades/actividades/:actividadId/rendir` (reemplaza el placeholder de
    `US-3.4.1`/`US-3.4.5` en `router.tsx` — no se usa el patrón `:actividadId` en la raíz de
    `/mis-actividades/` que proponía la tabla de artefactos de la spec, sino el ya vigente en
    el repo)
  - Al montar: `iniciarEvaluacion(actividadId)` (idempotente). Si `estado === "Suspendida"` →
    `navigate` a la pantalla de suspendida (`replace: true`, evita loop de historial). Si
    `ApiError.status === 422` (`FueraDePeriodo`) → `navigate` a `#est-fuera-periodo` existente
    (`US-3.4.5`)
  - Estado local: índice de pregunta actual (primera no respondida al cargar, o la última si
    ya están todas), set de `preguntasRespondidas` (inicializado desde la response)
  - Card de la pregunta actual: enunciado + opciones — radios si `opciones !== null` (Opción
    Múltiple), botones Verdadero/Falso si `opciones === null`
  - Puntos de navegación (`.dot`-equivalente): verde = respondida, azul = actual, gris =
    pendiente — clic navega sin confirmar
  - "Anterior"/"Confirmar y siguiente": confirmar llama `registrarRespuesta(evaluacionId,
    preguntaId, contenido)`, marca la pregunta como respondida localmente y avanza (clamp en la
    última pregunta — finalizar es alcance de `US-3.4.7`)
  - "Pausar y salir" (header): `suspenderEvaluacion(evaluacionId)` → navega a la pantalla de
    suspendida
  - Barra de progreso + contador "Pregunta N de {cantidad}" + hint de confiabilidad (texto
    estático del wireframe §3.3)
  - Ninguna opción indica si es correcta (ya garantizado por el backend — `ContenidoPregunta`
    nunca expone qué opción es correcta)

### 6. Frontend — Pantalla "Evaluación suspendida" (`#est-suspendida`)
- [x] `frontend/src/pages/EvaluacionSuspendida.tsx` (nueva)
  - Ruta nueva: `/mis-actividades/actividades/:actividadId/suspendida`
  - Al montar: `iniciarEvaluacion(actividadId)` (idempotente, mismo criterio que
    `RendirEvaluacion` — permite refrescar la página sin perder el evaluacionId) para obtener
    `evaluacionId` y la cantidad de `preguntasRespondidas`
  - Mensaje: "Guardamos tus N respuestas..." + alerta informativa sobre pausa automática por
    inactividad (texto estático del wireframe §3.4)
  - "Continuar": `reanudarEvaluacion(evaluacionId)` → navega de vuelta a `#est-rendir`

### 7. Integración — Rutas
- [x] `frontend/src/router.tsx`
  - Reemplaza el elemento placeholder (`ActividadEvaluativaPlaceholder`) de
    `/mis-actividades/actividades/:actividadId/rendir` por `<RendirEvaluacion />`
  - Agrega `/mis-actividades/actividades/:actividadId/suspendida` con `<EvaluacionSuspendida />`
    (mismo guard `RequireRole rol="estudiante"`)
  - La ruta de revisión (`.../evaluaciones/:evaluacionId/revision`) queda sin tocar — alcance de
    `US-3.4.7`

**Estado:** 7/7 tareas completadas
