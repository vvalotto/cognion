# Reporte de Implementación: US-3.4.6

## Resumen Ejecutivo

- **Historia de Usuario:** US-3.4.6 — Estudiante rinde su evaluación, responde, pausa y reanuda
- **Puntos estimados:** 8
- **Estado:** ✅ COMPLETADO
- **Fecha completado:** 2026-08-31
- **Spec:** `docs/specs/inc3/US-3.4.6.md`

Sexta US de la Iteración 4 del Incremento 3 (frontend, RNF Confiabilidad/RF-12). Cierra el
tramo central del flujo del Estudiante: responder preguntas una a una con persistencia atómica
por respuesta, pausar y reanudar sin perder nada, y reconexión idempotente ante un corte de
conexión. Consume `US-3.1.3` (iniciar/reconectar), `US-3.2.1` (registrar respuesta) y `US-3.2.2`
(suspender/reanudar), ya implementadas en el backend — sin cambiar su comportamiento.

---

## Decisión de diseño (desvío respecto de la tabla "Artefactos a modificar" de la spec)

La spec asignaba el poblado de `enunciado`/`opciones`/`preguntas_respondidas` a
`use_cases/iniciar_evaluacion.py`. Ese Use Case devuelve la entidad `Evaluacion` (dominio
puro, sin conocer texto de preguntas — mezclarlo violaría la regla de capas de `CLAUDE.md`). El
punto real donde se construye `EvaluacionResponse` es `_a_response()` en
`frameworks/api/evaluaciones_router.py`, reusado por los 4 endpoints que devuelven ese schema
(`iniciar`/`suspender`/`reanudar`/`finalizar`). El enriquecimiento se agregó ahí, aplicado a los
4 por consistencia (una consulta más al puerto ya existente, sin impacto de performance a esta
escala). `PreguntaConsultaPort` se inyectó como dependencia de FastAPI separada del router (no
como 6ª dependencia de `EvaluacionesController`, que ya tenía 5 Use Cases inyectados) para no
repetir el patrón de CRITICAL de CBO ya visto en `US-2.1.2`/`US-2.1.5`/`US-2.1.6`/`US-3.1.3`/
`US-3.2.1`. Plan completo y aprobado: `docs/plans/inc3/US-3.4.6-plan.md`.

---

## Componentes Implementados

### BC Actividad Evaluativa (Backend)

- ✅ **`ContenidoPregunta`** (`entities/ports/pregunta_consulta_port.py`, nuevo) — VO
  `frozen`: `texto`, `opciones: list[str] | None` (`None` para Verdadero/Falso), sin exponer
  cuál opción es correcta
- ✅ **`PreguntaConsultaPort.obtener_contenido()`** (nuevo método abstracto) — cuarto método del
  puerto, distinto de `obtener_detalle_correccion()` (esa sí expone la respuesta correcta, no
  debe reusarse antes de finalizar)
- ✅ **`PreguntaConsultaPortInProcess.obtener_contenido()`** (implementación) — reusa
  `_pregunta_repositorio.obtener_por_id()`, mismo criterio defensivo que los métodos existentes
- ✅ **`PreguntaAsignadaResponse`** (schema, ampliado) — `+enunciado: str`,
  `+opciones: list[str] | None`
- ✅ **`EvaluacionResponse`** (schema, ampliado) — `+preguntas_respondidas: list[UUID]` (ids
  únicos con `Respuesta` confirmada, sin duplicados ante reintentos)
- ✅ **`get_pregunta_consulta_port`** (`frameworks/dependencies.py`, nuevo) — dependencia
  FastAPI separada, no agregada al `EvaluacionesController`
- ✅ **`_a_response()`** (`frameworks/api/evaluaciones_router.py`, modificado) — pasa a `async`,
  arma `enunciado`/`opciones` por cada `PreguntaAsignada` y `preguntas_respondidas` desde
  `evaluacion.respuestas`; los 4 endpoints que la llaman ahora inyectan
  `Depends(get_pregunta_consulta_port)` y hacen `await`

### Frontend

- ✅ **`RendirEvaluacion.tsx`** (nueva) — reemplaza el placeholder de
  `/mis-actividades/actividades/:actividadId/rendir` (`US-3.4.1`/`US-3.4.5`); al montar llama
  `iniciarEvaluacion()` (idempotente), redirige a la pantalla de suspendida si
  `estado === "Suspendida"` o a fuera-de-período ante un 422; card de la pregunta actual
  (radios para Opción Múltiple, Verdadero/Falso con dos botones), puntos de navegación
  verde/azul/gris, "Anterior"/"Confirmar y siguiente", "Pausar y salir" en el header, barra de
  progreso y hint de confiabilidad
- ✅ **`EvaluacionSuspendida.tsx`** (nueva) — ruta nueva
  `/mis-actividades/actividades/:actividadId/suspendida`; llama `iniciarEvaluacion()`
  (idempotente, resiliente a refresh) para obtener `evaluacionId` y la cantidad de respuestas
  guardadas; "Continuar" llama `reanudarEvaluacion()` y vuelve a `#est-rendir`
- ✅ **`actividad-evaluativa-api.ts`** (extendido) — `PreguntaAsignadaResponse`
  `+enunciado`/`+opciones`, `EvaluacionResponse` `+preguntasRespondidas`, sin endpoints nuevos
  (el cliente API de `US-3.4.1` ya cubría todo lo necesario)
- ✅ **`router.tsx`** — reemplaza el placeholder de `/rendir` + agrega la ruta de `/suspendida`,
  mismo guard `RequireRole rol="estudiante"`

---

## Métricas de Calidad

| Métrica | Valor | Umbral | Estado |
|---------|-------|--------|--------|
| Pylint (archivos tocados) | 9.97/10 | ≥ 8.0 | ✅ |
| Complejidad Ciclomática (máx/función) | 5 | ≤ 10 | ✅ |
| Índice de Mantenibilidad (promedio archivos tocados) | 66.68 | > 20 | ✅ |
| Cobertura (`src/actividad_evaluativa`, excluye `frameworks/*`) | 99.78% | ≥ 95% | ✅ |
| mypy (`src/` completo) | 0 errores (189 archivos) | 0 errores | ✅ |
| Frontend — oxlint | 0 errores | 0 errores | ✅ |
| Frontend — `tsc --noEmit` | 0 errores | 0 errores | ✅ |

**Estado General:** ✅ APROBADO — `quality/reports/inc3/US-3.4.6-quality.json`

### Detalle de CodeGuard

> Reporte generado con `--analysis-type full`. Primera US en correr `vulture`/`codespell`
> realmente presentes en el `PATH` del subproceso (corridas anteriores mostraban "not
> installed" en vez del resultado real). Los 6 errors + 101 warnings de `DeadCode` son falsos
> positivos sistemáticos de vulture (60% de confianza) sobre parámetros de métodos
> `@abstractmethod`, campos de `BaseModel` de Pydantic y campos de `@dataclass` — se repiten
> sobre clases preexistentes no tocadas por esta US. Nada de lo señalado es código muerto real:
> todo está ejercitado por los 354 tests que pasan. Los 11 warnings de `Spelling` son ruido de
> `codespell` (orientado a inglés) sobre palabras en español de los docstrings. El único warning
> de `PEP8` es una línea de import preexistente de `US-3.4.5`, no tocada acá. Sugerido como
> tarea técnica futura (whitelist de vulture) — no se resuelve en esta US para no mezclar
> alcance.

| Check | Errors | Warnings | Infos |
|-------|--------|----------|-------|
| Security | 0 | 0 | 5 |
| PEP8 | 0 | 1 (línea preexistente) | 4 |
| Complexity | 0 | 0 | 5 |
| DeadCode | 6 (falsos positivos vulture) | 101 (ídem) | 1 |
| Maintainability | 0 | 0 | 5 |
| Pylint | 0 | 0 | 5 |
| Spelling | 0 | 11 (falsos positivos codespell/ES) | 1 |
| Types | 0 | 0 | 5 |
| UnusedImports | 0 | 0 | 5 |

Fuente: `quality/reports/inc3/US-3.4.6-codeguard.json`.

---

## Tests Implementados

### Tests Unitarios (7 tests nuevos)

- ✅ `test_evaluaciones_router_a_response.py` (7 tests) — enriquece enunciado/opciones de
  Opción Múltiple, `opciones` `None` en Verdadero/Falso, ninguna opción expone la correcta,
  `preguntas_respondidas` vacía/con datos/sin duplicados ante reintentos, preserva el resto de
  los campos de `EvaluacionResponse`
- `tests/unit/inc3/_fakes.py` (modificado) — `FakePreguntaConsultaPort.obtener_contenido()`,
  requerido por el nuevo método abstracto del puerto

### Tests de Integración (3 tests nuevos)

- ✅ `test_evaluaciones_api_integration.py` — `TestRendirEvaluacionAPIIntegration`: preguntas
  asignadas traen enunciado/opciones sin marcar la correcta (Opción Múltiple + Verdadero/Falso
  reales vía API), confirmar una respuesta la refleja en `preguntas_respondidas` tras
  reconexión, pausar y reanudar conserva el set y las respuestas

### Escenarios BDD (5 escenarios)

- ✅ `US-3.4.6-rendir-evaluacion.feature`
  - Confirmar una respuesta
  - Reconexión sin pérdida
  - Pausar y salir
  - Reanudar desde suspendida
  - El contenido de la pregunta no expone la respuesta correcta

### Tests de Frontend (10 tests nuevos)

- ✅ `RendirEvaluacion.test.tsx` (7 tests) — enunciado/opciones sin marcar la correcta, confirmar
  y avanzar, reconexión con respuestas previas marcadas, pausar y navegar a suspendida, redirect
  si ya está suspendida al entrar, redirect a fuera de período (422), pregunta Verdadero/Falso
- ✅ `EvaluacionSuspendida.test.tsx` (3 tests) — cantidad de respuestas guardadas, continuar
  reanuda y navega, mensaje de pausa automática

**Todos los tests pasando:** ✅ 355/355 unit backend, 230/230 integration backend, 71/71 BDD —
todas sin regresiones. 221/221 frontend sin regresiones.

---

## Archivos Creados/Modificados

### Código de Producción — Nuevo

- `frontend/src/pages/RendirEvaluacion.tsx`
- `frontend/src/pages/EvaluacionSuspendida.tsx`

### Código de Producción — Modificado

- `src/actividad_evaluativa/entities/ports/pregunta_consulta_port.py`
- `src/actividad_evaluativa/frameworks/adapters/pregunta_consulta_port_in_process.py`
- `src/actividad_evaluativa/frameworks/api/schemas.py`
- `src/actividad_evaluativa/frameworks/api/evaluaciones_router.py`
- `src/actividad_evaluativa/frameworks/dependencies.py`
- `frontend/src/lib/actividad-evaluativa-api.ts`
- `frontend/src/router.tsx`

### Tests

- `tests/unit/inc3/test_evaluaciones_router_a_response.py` (nuevo)
- `tests/unit/inc3/_fakes.py` (modificado — `FakePreguntaConsultaPort.obtener_contenido`)
- `tests/integration/inc3/test_evaluaciones_api_integration.py` (modificado —
  `TestRendirEvaluacionAPIIntegration` + helper `_crear_pregunta_opcion_multiple`)
- `tests/features/inc3/US-3.4.6-rendir-evaluacion.feature` (nuevo)
- `tests/step_defs/inc3/test_us_3_4_6_steps.py` (nuevo)
- `frontend/src/pages/RendirEvaluacion.test.tsx` (nuevo)
- `frontend/src/pages/EvaluacionSuspendida.test.tsx` (nuevo)

### Documentación / Infra

- `docs/specs/inc3/US-3.4.6.md` (preexistente, redactada antes de esta ejecución)
- `docs/plans/US-3.4.6-context.md`, `docs/plans/inc3/US-3.4.6-plan.md`
- `CHANGELOG.md` (entrada nueva bajo `[Unreleased]`)
- `docs/reports/inc3/US-3.4.6-report.md` (este archivo)
- `quality/reports/inc3/US-3.4.6-quality.json`, `US-3.4.6-codeguard.json`, `US-3.4.6-pylint.json`,
  `US-3.4.6-coverage.json`

---

## Criterios de Aceptación

- [x] Confirmar una respuesta la persiste de inmediato y avanza a la siguiente pregunta
- [x] Reconexión (recarga o reingreso posterior) retoma la misma `Evaluacion` con las
  respuestas ya marcadas, sin generar un nuevo set de preguntas
- [x] "Pausar y salir" suspende la evaluación y navega a la pantalla de suspendida
- [x] "Continuar" desde suspendida reanuda en el mismo punto donde quedó
- [x] Ninguna opción indica si es correcta al responder — el contenido de la pregunta nunca
  expone la respuesta correcta

**Todos los criterios cumplidos:** ✅

---

## Próximos Pasos

- [ ] Implementar `US-3.4.7` (Estudiante finaliza su evaluación y ve la revisión completa) —
  cierra la Iteración 4 y el Incremento 3 completo (backend + frontend)
- [ ] Evaluar whitelist de vulture a nivel de proyecto (tarea técnica sugerida, chip
  `task_0f9e8eb4`) para que el check `DeadCode` de codeguard deje de reportar ruido sobre
  métodos ABC/Pydantic/dataclass

---

## Lecciones Aprendidas

- ✅ Reusar el cliente API de frontend existente (`actividad-evaluativa-api.ts`, sin endpoints
  nuevos del lado UI) redujo la Fase 3 de frontend a solo 2 pantallas + rutas — todo el trabajo
  de red ya estaba resuelto desde `US-3.4.1`.
- ✅ Separar `PreguntaConsultaPort` como dependencia de FastAPI propia del router, en vez de
  sumarla al `EvaluacionesController` ya cargado con 5 Use Cases, evitó de entrada el patrón de
  CRITICAL de CBO que apareció repetidas veces en incrementos anteriores.
- 💡 Primera US en correr `codeguard --analysis-type full` con `vulture`/`codespell` realmente
  en el `PATH` del subproceso — reveló que el patrón "not installed" de corridas anteriores
  enmascaraba, no la ausencia de hallazgos, sino falsos positivos sistemáticos de vulture sobre
  métodos ABC/Pydantic/dataclass en todo el BC. Documentado en `quality.json` y como sugerencia
  de tarea técnica futura.

---

**Reporte generado automáticamente por Claude Code**
**Fecha:** 2026-08-31
