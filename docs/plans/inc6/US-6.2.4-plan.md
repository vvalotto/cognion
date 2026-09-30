# Plan de Implementación: US-6.2.4 - Estudiante responde una pregunta en vivo

**Patrón:** clean-architecture (entities → use_cases → interface_adapters → frameworks, BC-first)
**Producto:** cognion — BC `actividad_evaluativa`

## Decisiones de diseño (a confirmar en este checkpoint)

1. **Validación de la sesión** (`ActividadEvaluativaEnVivo.validar_para_responder(pregunta_id,
   ahora) -> float`, helper a nivel módulo para no sumar CBO a la clase). No muta. Orden:
   `estado != EnCurso` → `SesionNoEnCurso`; `pregunta_id` ≠ actual → `PreguntaNoActual`;
   `pregunta_actual_cerrada` → `PreguntaYaCerrada`; `not opciones_mostradas` →
   `OpcionesNoMostradasTodavia`; `tiempo > tiempo_limite` → `TiempoAgotado` (INV-AEV-08).
   Devuelve `tiempo_respuesta_segundos = ahora − opciones_mostradas_en`.
2. **Aggregate `ParticipacionEnVivo`:** `RespuestaEnVivo` (VO frozen: `pregunta_id`, `contenido`,
   `es_correcta`, `tiempo_respuesta_segundos`, `puntaje`); `respuestas: list[RespuestaEnVivo]`;
   `puntaje_acumulado` (property); `responder(...)` levanta `RespuestaYaRegistrada` (INV-AEV-07) si
   ya hay una para esa pregunta, si no la agrega. `reconstruir()` pasa a hacer dispatch por
   `event_type` (`EstudianteUnido` arma la base; `RespuestaEnVivoRegistrada` suma la respuesta).
3. **Evento `RespuestaEnVivoRegistrada`** con `desde_participacion(...)`, payload según la spec
   (`sesion_id`, `estudiante_id`, `pregunta_id`, `contenido`, `es_correcta`,
   `tiempo_respuesta_segundos`, `puntaje`, `ocurrido_en`).
4. **Use Case** `ResponderPreguntaEnVivoUseCase.execute(sesion_id, estudiante_id, pregunta_id,
   contenido)` → `ResultadoRespuestaEnVivo(es_correcta, puntaje, puntaje_acumulado)`:
   `load` sesión (`SesionNoExiste`) → `load` participación (`ParticipacionNoExiste`) →
   `validar_para_responder` → `evaluar_correccion` + `obtener_niveles` → `calcular_puntaje` →
   `participacion.responder` → `proyecciones.registrar_respuesta` (sin commit) → `append` con
   `expected_sequence_number = len(eventos_participacion)`. `ConcurrenciaOptimistaError` →
   `descartar_pendientes()` + `RespuestaYaRegistrada` (contrato de `US-6.2.3`). Después de
   persistir: `cantidad_respuestas` (query port) y broadcast
   `{"tipo": "conteo_respuestas_actualizado", "pregunta_actual_indice": N, "cantidad_respuestas": M}`
   — sin desglose por opción; canal best-effort.
5. **Clave de la opción en la proyección:** `str(opcion_indice)` para opción múltiple;
   `"verdadero"`/`"falso"` para V/F (`valor` bool). Helper puro en el Use Case.
6. **Forma de `contenido`:** validada en el borde HTTP (schema Pydantic): exactamente
   `{"opcion_indice": int}` o `{"valor": bool}`, si no → 422 de FastAPI. No agrega excepción de
   dominio nueva (la spec no la lista).
7. **Errores nuevos** en `errors.py`: `ParticipacionNoExiste`, `PreguntaNoActual`,
   `OpcionesNoMostradasTodavia`, `PreguntaYaCerrada`, `TiempoAgotado`, `RespuestaYaRegistrada`
   (`SesionNoEnCurso` ya existe). HTTP: `SesionNoExiste`/`ParticipacionNoExiste` → 404, el resto → 422.
8. **Controller / CBO:** controller **propio** `ParticipacionesEnVivoController` (un solo use
   case, `responder`) en vez de sumar un 5° al `SesionesEnVivoController` — la spec lo anticipa y
   evita el patrón de CRITICAL de CBO ya visto. No cambia la firma del controller existente, así
   que no hay que tocar los 4 tests que lo construyen. El CBO real del Use Case (5 puertos +
   entidades) se confirma en el pre-push; si llega al umbral, se extraen helpers (payload/mensaje)
   como en `US-6.2.2`.
9. **Endpoint:** `POST /sesiones-en-vivo/{sesion_id}/responder`, rol `estudiante`, body
   `{pregunta_id, contenido}`, **200** `{es_correcta, puntaje, puntaje_acumulado}` (sin ranking).
   Vive en `sesiones_en_vivo_router.py`; dependency nueva `get_participaciones_en_vivo_controller`.
10. **Sin migración de DB** (tablas de `US-6.2.3` ya existen), sin cambios en `src/app.py`.

## Componentes a Implementar

### 1. Entities
- [x] `src/actividad_evaluativa/entities/errors.py`
  - los 6 errores nuevos
- [x] `src/actividad_evaluativa/entities/actividad_evaluativa_en_vivo.py`
  - `validar_para_responder(pregunta_id, ahora) -> float`
- [x] `src/actividad_evaluativa/entities/participacion_en_vivo.py`
  - `RespuestaEnVivo`, `responder()`, `puntaje_acumulado`, `reconstruir()` con dispatch
- [x] `src/actividad_evaluativa/entities/eventos_en_vivo.py`
  - `RespuestaEnVivoRegistrada` + `desde_participacion`

### 2. Use Case
- [x] `src/actividad_evaluativa/use_cases/responder_pregunta_en_vivo.py`
  - `ResponderPreguntaEnVivoUseCase`, `ResultadoRespuestaEnVivo`

### 3. Interface Adapter
- [x] `src/actividad_evaluativa/interface_adapters/controllers/participaciones_en_vivo_controller.py`
  - `ParticipacionesEnVivoController.responder(...)`

### 4. Frameworks
- [x] `src/actividad_evaluativa/frameworks/api/schemas.py`
  - `ResponderEnVivoRequest` (con validación de `contenido`), `RespuestaEnVivoResponse`
- [x] `src/actividad_evaluativa/frameworks/api/sesiones_en_vivo_router.py`
  - `POST /{sesion_id}/responder` (rol `estudiante`)
- [x] `src/actividad_evaluativa/frameworks/dependencies.py`
  - `get_participaciones_en_vivo_controller`

## Tests (Fases 4–6, no forman parte de las tareas de Fase 3)
- Unit: `validar_para_responder`, `responder()`/`reconstruir`, use case (Fakes; actualizar los
  Fakes de puertos si hace falta), controller.
- Integración: HTTP + WebSocket real + `concurrencia real` (60 respuestas simultáneas de 60
  estudiantes y doble envío del mismo) contra la DB. Recordar: vacía la DB local compartida.
- BDD: step defs de `tests/features/inc6/US-6.2.4-responder-pregunta-en-vivo.feature`.

**Estado:** ✅ COMPLETADO
**Fecha completado:** 2026-09-20
**Tareas:** 4/4 secciones completadas

## Desvíos respecto del plan

- Las 10 decisiones de diseño se implementaron como se aprobaron.
- Fuera del checklist:
  - `ActividadEvaluativaEnVivo.reconstruir()` aplica `PreguntaEnVivoCerrada` (marca
    `pregunta_actual_cerrada`) — sin eso `PreguntaYaCerrada` no se podía verificar de punta a
    punta antes de `US-6.2.5`, que es quien emite ese evento.
  - `execute` se partió en `_corregir` y `_persistir` (pylint R0914, too-many-locals).
  - Helpers nuevos en `tests/integration/inc6/_helpers.py`: `unirse_a_sesion`,
    `mostrar_opciones`, `sembrar_opciones_mostradas_hace`, `pregunta_actual_de`.
- Escenario "Una sesión en la pregunta 2": `AvanzarSiguientePregunta` es `US-6.2.6`, así que el
  step prepara la sesión en su pregunta actual y responde con el id de otra pregunta del set.
  Verifica `PreguntaNoActual` pero no con el estado literal del Gherkin.

## Métricas de Tiempo

Tiempos medidos por el tracker (PRIN-001). Detalle en `docs/reports/inc6/US-6.2.4-report.md`.

## Lecciones Aprendidas

- ✅ Un controller propio para las respuestas evitó tocar la firma de `SesionesEnVivoController`
  (4 tests menos que actualizar) y no llegó al umbral de CBO.
- ✅ La concurrencia real (60 respuestas simultáneas + doble envío) confirmó el contrato de
  atomicidad evento + proyección de `US-6.2.3` sin cambios.
- ⚠️ En el test de 60 respuestas, crear 60 cuentas (bcrypt) tarda más que el tiempo límite de la
  pregunta: las opciones se muestran **después** de unir a todos, si no todas dan `TiempoAgotado`.
- ⚠️ El flaky preexistente de `US-3.2.1` volvió a fallar en la suite completa, ajeno a esta US.
- ⚠️ Los errors de CodeGuard son timeouts de su check de pylint interno y un falso positivo de
  DeadCode (`cls` de un `@classmethod` validator de pydantic); pylint directo da 9.60/10.
