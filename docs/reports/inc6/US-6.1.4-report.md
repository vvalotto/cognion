# Reporte de Implementación: US-6.1.4

## Resumen Ejecutivo

- **Historia de Usuario:** US-6.1.4 — Docente inicia la sesión en vivo — se presenta la primera pregunta
- **Puntos estimados:** 3
- **Tiempo real:** ~21 min (tracker; incluye ~8 min de la suite completa con cobertura en Fase 7 — PRIN-001, tiempo real de ejecución del agente, no comparable contra estimación humana)
- **Estado:** ✅ COMPLETADO
- **Fecha completado:** 2026-09-19
- **Cierra:** la Iteración 1 del Incremento 6 (RF-08 + infraestructura WebSockets): crear → unirse → iniciar queda operable de punta a punta por HTTP + WebSocket

---

## Componentes Implementados

### Entities (`src/actividad_evaluativa/entities/`)

- ✅ **`ActividadEvaluativaEnVivo.iniciar()`** (`actividad_evaluativa_en_vivo.py`) — valida `estado == EnEspera` (si no, `SesionYaIniciada`, que cubre `EnCurso` y `Finalizada`) y transiciona a `EnCurso` con `pregunta_actual_indice = 0`, `opciones_mostradas = False`, `pregunta_actual_cerrada = False`. No exige participantes. Se suma `pregunta_actual()`
- ✅ **`reconstruir()`** — ahora toma `pregunta_actual_indice` del payload real de `SesionEnVivoIniciada` (default 0, para los streams sembrados con payload mínimo)
- ✅ **`SesionEnVivoIniciada`** (`eventos_en_vivo.py`) — segundo evento del stream: `pregunta_actual_indice`, y la pregunta tal como se presentó (`pregunta_id`, `enunciado`, `tipo`), **sin opciones**; `desde_sesion(...)`
- ✅ **`SesionYaIniciada`** (`errors.py`) — error de dominio nuevo

### Use Cases (`src/actividad_evaluativa/use_cases/`)

- ✅ **`IniciarSesionEnVivoUseCase`** (`iniciar_sesion_en_vivo.py`) — reconstruye la sesión, la inicia, obtiene el enunciado de la primera pregunta por `PreguntaConsultaPort`, persiste el evento con `expected_sequence_number = len(eventos)` y recién entonces publica por `CanalTiempoRealPort`. Traduce `ConcurrenciaOptimistaError` a `SesionYaIniciada` (carrera de dos inicios). Deriva `tipo` de `opciones` (`None` = Verdadero/Falso) sin tocar el puerto

### Interface Adapters

- ✅ **`SesionesEnVivoController.iniciar(...)`** — el controller pasa a inyectar 3 use cases (cambio de firma del constructor)

### Frameworks (`src/actividad_evaluativa/frameworks/`)

- ✅ **`POST /sesiones-en-vivo/{sesion_id}/iniciar`** (`api/sesiones_en_vivo_router.py`, rol `docente`) — 200 con el estado actualizado; `SesionNoExiste` → 404, `SesionYaIniciada` → 422. Helper `_a_sesion_response` compartido con `crear`
- ✅ **`SesionEnVivoResponse.pregunta_actual_indice`** (`api/schemas.py`) — campo opcional, `None` mientras la sesión está `EnEspera` (cambio aditivo: no rompe la respuesta de creación de `US-6.1.2`)
- ✅ **Wiring** del tercer use case en `dependencies.py`

**Mensaje de broadcast** a todos los conectados (Docente, Estudiantes, proyección):
`{"tipo": "pregunta_presentada", "pregunta_actual_indice": 0, "pregunta": {"pregunta_id", "enunciado", "tipo"}}` — solo el enunciado, sin opciones (las revela `MostrarOpcionesDeLaPregunta`, Iteración 2).

---

## Métricas de Calidad

| Métrica | Valor | Objetivo | Estado |
|---------|-------|----------|--------|
| **Pylint** | 9.89/10 | ≥ 8.0 | ✅ |
| **Complejidad Ciclomática (máx/función)** | 5 (promedio 1.57) | ≤ 10 | ✅ |
| **Índice de Mantenibilidad (mín)** | 59.22 (promedio 80.59) | > 20 | ✅ |
| **Coverage (`entities`/`use_cases`/`interface_adapters` del BC)** | 100% | ≥ 95% | ✅ |
| **CodeGuard** (8 archivos analizados) | 0 errors, 230 warnings | 0 CRITICAL | ✅ |

**Estado General:** ✅ APROBADO (`quality/reports/inc6/US-6.1.4-quality.json`)

> `frameworks/*` está excluido del gate de coverage por `pyproject.toml` (mismo criterio en todos
> los BCs). El router se valida con 34 tests de integración contra la DB real y con BDD.

### Detalle de CodeGuard

> Generado con `--analysis-type full` y `.venv/bin` en el `PATH`, en serie y con la máquina
> libre (`quality/reports/inc6/US-6.1.4-codeguard.json`).

| Check | Errors | Warnings | Infos |
|-------|--------|----------|-------|
| Security | 0 | 0 | 8 |
| PEP8 | 0 | 1 | 7 |
| Complexity | 0 | 0 | 8 |
| DeadCode | 0 | 168 | 0 |
| Maintainability | 0 | 0 | 8 |
| Pylint | 0 | 0 | 8 |
| Spelling | 0 | 61 | 1 |
| Types | 0 | 0 | 8 |
| UnusedImports | 0 | 0 | 8 |

`DeadCode` (168) y `Spelling` (61) son ruido conocido: el primero analiza archivo por archivo
sin ver usos cross-módulo, el segundo compara texto en español con un diccionario en inglés. El
único warning de `PEP8` es un import preexistente (`dependencies.py:57`). Una corrida
intermedia mostró un timeout puntual de pylint dentro de `UnusedImports`; no se repitió en la
final.

---

## Tests Implementados

### Tests Unitarios (19 tests nuevos, `tests/unit/inc6/`)

- ✅ `test_actividad_evaluativa_en_vivo.py` (ampliado) — `iniciar()` (transición, rechazo desde `EnCurso` y `Finalizada`, no muta si se rechaza), `pregunta_actual()`, `reconstruir` con payload real y con payload mínimo sembrado
- ✅ `test_participacion_en_vivo.py` (ampliado) — `SesionYaIniciada`, `SesionEnVivoIniciada.desde_sesion` (y su rechazo sin iniciar)
- ✅ `test_iniciar_sesion_en_vivo_use_case.py` — segundo evento persistido con la pregunta presentada, broadcast solo con enunciado y sin opciones, `tipo` derivado de `opciones`, inicio sin participantes, rechazos (inexistente, segundo inicio sin persistir ni publicar, sesión finalizada, carrera de dos inicios); controller
- ✅ Se actualizaron 2 tests existentes por la nueva firma del controller

**Estado:** 74/74 pasando en `tests/unit/inc6/` (19 nuevos). Cobertura 100% de los archivos
nuevos y modificados de `entities`/`use_cases`/`interface_adapters`.

### Tests de Integración (10 tests nuevos, `tests/integration/inc6/`)

- ✅ `test_sesiones_en_vivo_iniciar_router.py` — inicio con un estudiante unido (verifica el segundo evento y su payload en `events`), sin participantes, sesión ya iniciada (422, sin evento extra), sesión finalizada, inexistente (404), rol Estudiante (403), sin token, **dos inicios simultáneos contra la DB (uno 200, otro 422)**, un estudiante se une después de iniciada; y **broadcast por WebSocket real a Docente y Estudiante** recibiendo el mismo enunciado sin opciones
- ✅ `_helpers.iniciar_sesion` (nuevo); los tests de `US-6.1.3` que necesitaban `EnCurso` migraron al endpoint real

**Estado:** 34/34 pasando en `tests/integration/inc6/` (10 nuevos)

### Escenarios BDD (5 escenarios nuevos, `tests/features/inc6/US-6.1.4-iniciar-sesion-en-vivo.feature`)

- ✅ Inicio exitoso (con Docente y Estudiante conectados) · inicio sin estudiantes · sesión ya iniciada · sesión inexistente · rechazo por rol — step defs en `tests/step_defs/inc6/test_us_6_1_4_steps.py`

**Estado:** 15/15 pasando en `tests/step_defs/inc6/` (5 nuevos; los de `US-6.1.3` siguen en verde tras migrar a `iniciar_sesion`)

**Suite completa del proyecto** (`tests/`, sin acotar, corrida antes de `codeguard`): **1319
passed, 1 failed** en 7 min 57 s. El fallo es
`tests/step_defs/inc3/test_us_3_2_1_steps.py::test_rechazo_fuera_del_período_vigente`, el flaky
preexistente documentado en `CLAUDE.md`: su setup recibió `FueraDePeriodo` al iniciar una
evaluación en una actividad de período abierto, sin relación con el modo en vivo. Aislado pasa 3
de 3 (la corrida completa de `US-6.1.3` lo había pasado, así que sigue siendo intermitente).

---

## Archivos Creados/Modificados

### Código de Producción

- `src/actividad_evaluativa/use_cases/iniciar_sesion_en_vivo.py` (nuevo)
- `src/actividad_evaluativa/entities/actividad_evaluativa_en_vivo.py` (modificado — `iniciar`, `pregunta_actual`, `reconstruir`)
- `src/actividad_evaluativa/entities/eventos_en_vivo.py` (modificado — `SesionEnVivoIniciada`)
- `src/actividad_evaluativa/entities/errors.py` (modificado — `SesionYaIniciada`)
- `src/actividad_evaluativa/interface_adapters/controllers/sesiones_en_vivo_controller.py` (modificado)
- `src/actividad_evaluativa/frameworks/api/sesiones_en_vivo_router.py`, `schemas.py`, `dependencies.py` (modificados)

### Tests

- `tests/unit/inc6/test_iniciar_sesion_en_vivo_use_case.py` (nuevo)
- `tests/unit/inc6/test_actividad_evaluativa_en_vivo.py`, `test_participacion_en_vivo.py`, `test_crear_sesion_en_vivo_use_case.py`, `test_unirse_a_sesion_en_vivo_use_case.py` (modificados)
- `tests/integration/inc6/test_sesiones_en_vivo_iniciar_router.py` (nuevo); `_helpers.py`, `test_sesiones_en_vivo_unirse_router.py` (modificados)
- `tests/features/inc6/US-6.1.4-iniciar-sesion-en-vivo.feature` (nuevo)
- `tests/step_defs/inc6/test_us_6_1_4_steps.py` (nuevo); `test_us_6_1_3_steps.py` (modificado)

### Documentación

- `docs/plans/inc6/US-6.1.4-context.md`, `US-6.1.4-plan.md`
- `docs/specs/inc6/US-6.1.4.md` (estado → `Implementada`)
- `docs/reports/inc6/US-6.1.4-report.md` (este archivo)
- `quality/reports/inc6/US-6.1.4-quality.json`, `-codeguard.json`, `-coverage.json`

---

## Desafíos y Soluciones

### Desafío 1: `tipo` pedido por la spec, pero el puerto no lo expone

**Descripción:** La spec pide `tipo` en el payload de `SesionEnVivoIniciada`, pero
`PreguntaConsultaPort.obtener_contenido()` devuelve solo `texto` y `opciones`.

**Solución:** Se deriva en el Use Case (`opciones is None` ⇒ `verdadero_falso`, si no
`opcion_multiple`), que es exactamente lo que el propio puerto ya documenta. Evita ensanchar un
puerto y un dataclass usados en varios lugares y sus Fakes por un dato derivable. Reversible si
aparece un tercer tipo. Las opciones se descartan: no viajan ni se persisten.

### Desafío 2: Dos Docentes inician a la vez

**Descripción:** Sin control, el segundo inicio podía propagar un error de infraestructura (500).

**Solución:** El `append` usa `expected_sequence_number = len(eventos)`; el chequeo optimista del
event store deja ganar a uno y el use case traduce el `ConcurrenciaOptimistaError` a
`SesionYaIniciada` (422). Verificado con un Fake y con una carrera real de dos requests
simultáneos contra la DB.

### Desafío 3: Un `assert` en código de producción

**Descripción:** `SesionEnVivoIniciada.desde_sesion` usaba un `assert` para estrechar el tipo de
`pregunta_actual_indice`, que el check de seguridad de CodeGuard suele marcar.

**Solución:** Se reemplazó por `pregunta_actual()` (que ya levanta si la sesión no fue iniciada)
y `pregunta_actual_indice or 0`, sin `assert`.

---

## Cambios no Previstos

- Ningún desvío de diseño respecto del plan aprobado.
- Se agregó una prueba de carrera real de dos inicios simultáneos contra la DB (no estaba en el
  plan, que preveía solo el unitario).
- Se acortaron dos docstrings de más de 100 caracteres (`schemas.py`, `actividad_evaluativa_en_vivo.py`).

---

## Criterios de Aceptación

- [x] Inicio exitoso: estado `EnCurso` con `pregunta_actual_indice = 0` y todos los conectados reciben el enunciado de la primera pregunta, sin opciones
- [x] Inicio sin ningún Estudiante unido: se acepta igual, el dominio no exige un mínimo
- [x] Sesión ya iniciada → `SesionYaIniciada` (422)
- [x] Sesión inexistente → `SesionNoExiste` (404)
- [x] Rechazo por rol Estudiante → 403

**Estado:** 5/5 cumplidos

---

## Próximos Pasos

- [ ] **Iteración 1 del Incremento 6 completa** (`US-6.1.1` a `US-6.1.4`): pendiente la verificación de cierre de iteración (UAT de Capa 1/Capa 2 y revisión manual), antes de que RF-08 pase a Implementado en `docs/traceability/matrix.md`
- [ ] Iteración 2 del Incremento 6: la dinámica pregunta por pregunta (`MostrarOpcionesDeLaPregunta`, `ResponderPreguntaEnVivo`, `CerrarPreguntaActual`, `AvanzarSiguientePregunta`, `FinalizarSesionEnVivo`, ranking) — `SesionEnVivoFinalizada` todavía solo se siembra en los tests
- [ ] La sala de espera del Docente muestra solo ids de estudiantes: mostrar nombres requerirá un puerto a Identidad, alcance del frontend (todavía sin iteración asignada en `inc6-candidatas.md`)
- [ ] Sin ownership de sesión: cualquier Docente autenticado puede iniciar cualquier sesión (mismo criterio que el resto de los endpoints de Actividad Evaluativa; la spec no lo define)

---

## Lecciones Aprendidas

- ✅ Grepear los `Controller(` de los tests antes de cambiar la firma evitó repetir el test roto de `US-6.1.3`.
- ✅ Con el endpoint real disponible, los tests que sembraban `SesionEnVivoIniciada` pasaron a usarlo; solo `Finalizada` sigue sembrada.
- ✅ Traducir `ConcurrenciaOptimistaError` a `SesionYaIniciada` cierra la carrera sin un 500, verificado contra la DB real.
- ⚠️ El flaky de `US-3.2.1` volvió a fallar en la suite completa: no es de esta US, pero sigue siendo ruido y conviene resolverlo.
- ⚠️ `codeguard` puede dar un timeout puntual de pylint (>5s) aun en serie y con la máquina libre; repetir antes de darlo por hallazgo.
- 💡 `TestClient` permite abrir dos WebSockets (Docente y Estudiante) y verificar que ambos reciben el mismo mensaje del `POST`.

---

**Reporte generado automáticamente por Claude Code**
**Fecha:** 2026-09-19
