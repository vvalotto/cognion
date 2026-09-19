# Plan de Implementación: US-6.1.4 - Docente inicia la sesión en vivo

**Patrón:** clean-architecture (entities → use_cases → interface_adapters → frameworks, BC-first)
**Producto:** cognion — BC `actividad_evaluativa`

## Decisiones de diseño (a confirmar en este checkpoint)

1. **`tipo` del payload se deriva en el Use Case, sin tocar `PreguntaConsultaPort`.** La spec pide
   `pregunta_id`, `enunciado` y `tipo`, pero `obtener_contenido()` devuelve solo `texto` y
   `opciones`. El propio puerto ya documenta que `opciones is None` ⇒ Verdadero/Falso, así que
   `tipo` = `"verdadero_falso"` si `opciones is None`, si no `"opcion_multiple"`. Se descartan las
   opciones (no viajan ni se persisten: las revela `MostrarOpcionesDeLaPregunta`, Iteración 2).
   Evita ensanchar un puerto y un frozen dataclass usados en 3 lugares y sus Fakes, por un dato
   derivable. Reversible: si aparece un tercer tipo, se agrega el campo al puerto.
2. **Payload de `SesionEnVivoIniciada`:** `{sesion_id, pregunta_actual_indice: 0, pregunta:
   {pregunta_id, enunciado, tipo}, ocurrido_en}`. La pregunta se persiste **tal como se presentó**
   (no se relee del banco al reconstruir), igual criterio que las `Respuesta` de `Evaluacion`.
3. **`reconstruir()` ahora usa el payload real:** `SesionEnVivoIniciada` → `EnCurso` y
   `pregunta_actual_indice = payload.get("pregunta_actual_indice", 0)`. El default 0 mantiene
   compatibles los tests de `US-6.1.3` que siembran ese evento con payload mínimo.
   `SesionEnVivoFinalizada` no cambia (Iteración 2).
4. **`ActividadEvaluativaEnVivo.iniciar()`** valida y muta: `estado != EnEspera` →
   `SesionYaIniciada` (cubre `EnCurso` **y** `Finalizada`, como pide la spec); si no, pasa a
   `EnCurso`, `pregunta_actual_indice = 0`, `opciones_mostradas = False`,
   `pregunta_actual_cerrada = False`.
5. **Concurrencia:** dos `iniciar` simultáneos: el `append` usa `expected_sequence_number =
   len(eventos)`, así que el segundo choca con `ConcurrenciaOptimistaError`. Se traduce a
   `SesionYaIniciada` (es exactamente ese caso), en vez de propagar un 500.
6. **Mensaje de broadcast** a todos los conectados (§16, primera fila): `{"tipo":
   "pregunta_presentada", "pregunta_actual_indice": 0, "pregunta": {"pregunta_id", "enunciado",
   "tipo"}}`. Sin opciones. Se publica **después** de persistir; el canal es best-effort (nunca
   lanza), así que una falla de broadcast no revierte el inicio.
7. **Orden de validación:** `SesionNoExiste` → `SesionYaIniciada`. Iniciar con cero participantes
   se acepta (sin invariante nueva, como pide la spec).
8. **Endpoint:** `POST /sesiones-en-vivo/{sesion_id}/iniciar`, rol `docente`, sin body, **200** con
   el estado actualizado. `SesionNoExiste` → 404, `SesionYaIniciada` → 422. Se agrega
   `pregunta_actual_indice: int | None` (default `None`) a `SesionEnVivoResponse`; para la
   creación sigue en `None` (cambio aditivo, no rompe a `US-6.1.2`). El armado del response se
   extrae a un helper compartido por `crear` e `iniciar`.
9. **Controller:** `SesionesEnVivoController` pasa a **3 use cases**. Cambia la firma del
   constructor: hay que actualizar los 2 tests que lo construyen
   (`test_crear_sesion_en_vivo_use_case.py:135`, `test_unirse_a_sesion_en_vivo_use_case.py:222`)
   y `dependencies.py`. Grepeado de antemano (lección de `US-6.1.3`).
10. **CBO:** el use case depende de 3 puertos (`EventStorePort`, `PreguntaConsultaPort`,
    `CanalTiempoRealPort`); el evento se arma con un `desde_sesion(...)` como en `US-6.1.2`. Se
    verifica en el pre-push.
11. **Tests de `US-6.1.3`:** los escenarios de integración/BDD que necesitan `EnCurso` pasan a
    usar el endpoint real `iniciar` en vez de sembrar el evento (queda un helper `iniciar_sesion`).
    `Finalizada` sigue sembrada (Iteración 2). Los unitarios con Fakes no cambian.
12. **Fuera de alcance, para registrar:** cualquier Docente autenticado puede iniciar cualquier
    sesión — la spec no define ownership (mismo criterio que el resto de los endpoints de
    Actividad Evaluativa). No se agrega.

## Componentes a Implementar

### 1. Entities
- [x] `src/actividad_evaluativa/entities/errors.py`
  - `SesionYaIniciada(sesion_id)`
- [x] `src/actividad_evaluativa/entities/actividad_evaluativa_en_vivo.py`
  - `iniciar()` (valida `EnEspera`, transiciona) y `reconstruir()` con `pregunta_actual_indice`
- [x] `src/actividad_evaluativa/entities/eventos_en_vivo.py`
  - `SesionEnVivoIniciada` + `desde_sesion(sesion, enunciado, tipo)`

### 2. Use Case
- [x] `src/actividad_evaluativa/use_cases/iniciar_sesion_en_vivo.py`
  - `IniciarSesionEnVivoUseCase.execute(sesion_id)` → `ActividadEvaluativaEnVivo`
  - carga y reconstruye, `iniciar()`, obtiene enunciado, `append`, publica

### 3. Interface Adapter
- [x] `src/actividad_evaluativa/interface_adapters/controllers/sesiones_en_vivo_controller.py`
  - método `iniciar(sesion_id)`; constructor con 3 use cases

### 4. Frameworks
- [x] `src/actividad_evaluativa/frameworks/api/schemas.py`
  - `pregunta_actual_indice` opcional en `SesionEnVivoResponse`
- [x] `src/actividad_evaluativa/frameworks/api/sesiones_en_vivo_router.py`
  - `POST /{sesion_id}/iniciar` (rol `docente`), helper de response compartido
- [x] `src/actividad_evaluativa/frameworks/dependencies.py`
  - wiring del tercer use case

### 5. Integración
- [x] `src/app.py` sin cambios. Sin migración de DB.

## Tests (Fases 4–6, no forman parte de las tareas de Fase 3)
- Unit: `iniciar()`, `reconstruir` con payload real, evento, use case (`FakeCanalTiempoReal` y
  `FakePreguntaConsultaPort.contenidos` ya existen), controller; actualizar 2 tests por la firma.
- Integración: `test_sesiones_en_vivo_iniciar_router.py` (HTTP + broadcast a Docente **y**
  Estudiante por WebSocket real); `_helpers.iniciar_sesion`; migrar EnCurso de `US-6.1.3`.
- BDD: `tests/step_defs/inc6/test_us_6_1_4_steps.py` sobre
  `tests/features/inc6/US-6.1.4-iniciar-sesion-en-vivo.feature`.

**Estado:** ✅ COMPLETADO
**Fecha completado:** 2026-09-19
**Tareas:** 9/9 completadas (código: 1 tarea de Fase 3 que agrupa las 9 del checklist)

## Métricas de Tiempo

Tiempos reales medidos por el tracker (PRIN-001: no se comparan contra estimaciones humanas).

| Fase | Real |
|------|------|
| 0 Contexto | 25 s |
| 1 BDD | 19 s |
| 2 Plan | 1 min 54 s |
| 3 Implementación | 1 min 14 s |
| 4 Tests unitarios | 1 min 35 s |
| 5 Tests de integración | 47 s |
| 6 Validación BDD | 22 s |
| 7 Quality gates | 12 min 47 s (7 min 57 s solo la suite completa con cobertura) |
| 8 Documentación | ver reporte final (`docs/reports/inc6/US-6.1.4-report.md`) |

## Desvíos respecto del plan

- Ninguno de diseño: las 12 decisiones se implementaron como se aprobaron.
- Ajustes menores durante la implementación: se evitó un `assert` en `SesionEnVivoIniciada.
  desde_sesion` (lo marca el check de seguridad de CodeGuard; `pregunta_actual()` ya levanta si la
  sesión no fue iniciada) y se acortaron dos docstrings que superaban 100 caracteres.
- Fuera del checklist: se agregó una prueba de **carrera real** de dos inicios simultáneos contra
  la DB (uno gana con 200, el otro recibe 422), además del unitario con `FakeEventStore`.

## Lecciones Aprendidas

- ✅ Grepear los `Controller(` de los tests **antes** de cambiar la firma (lección de `US-6.1.3`)
  evitó repetir el test roto: los 2 usos estaban identificados desde el plan.
- ✅ Con el endpoint real disponible, los tests de `US-6.1.3` que sembraban `SesionEnVivoIniciada`
  a mano pasaron a usarlo (`_helpers.iniciar_sesion`); solo `Finalizada` sigue sembrada.
- ✅ Traducir `ConcurrenciaOptimistaError` a `SesionYaIniciada` cierra la carrera de dos Docentes
  sin un 500, y quedó verificado contra la DB real, no solo con un Fake.
- ⚠️ El flaky preexistente de `US-3.2.1` (`test_rechazo_fuera_del_período_vigente`) volvió a
  fallar en la suite completa tras pasar en la corrida anterior. No es de esta US (FueraDePeriodo
  en una actividad de período abierto); aislado pasa 3/3. Sigue siendo ruido en la suite.
- ⚠️ `codeguard` puede dar un timeout puntual de pylint (>5s) aun corrido en serie con la máquina
  libre; repetir la corrida antes de darlo por hallazgo (en la segunda salió 0 errores).
- 💡 `TestClient` permite abrir dos WebSockets (Docente y Estudiante) a la vez y verificar que
  ambos reciben el mismo mensaje del `POST`, sin fixtures async especiales.
