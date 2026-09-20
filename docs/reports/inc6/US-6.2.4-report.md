# Reporte de Implementación: US-6.2.4

## Resumen Ejecutivo

- **Historia de Usuario:** US-6.2.4 — Estudiante responde una pregunta en vivo
- **Puntos estimados:** 5 (la spec no lo declara)
- **Tiempo real:** ~46 min (tracker; ~27 min son la suite completa con cobertura y CodeGuard en Fase 7 — PRIN-001, tiempo real de ejecución del agente, no comparable contra estimación humana)
- **Estado:** ✅ COMPLETADO
- **Fecha completado:** 2026-09-20
- **Aporta:** el núcleo de RF-09/RF-10. El Estudiante responde tocando una opción y recibe al instante si acertó, los puntos de esa pregunta y su acumulado, sin ranking. Un solo intento por pregunta, tiempo medido por el servidor, proyecciones y evento confirmados juntos.

---

## Componentes Implementados

### Entities (`src/actividad_evaluativa/entities/`)

- ✅ **`ActividadEvaluativaEnVivo.validar_para_responder(pregunta_id, ahora)`** — no muta; rechaza con `SesionNoEnCurso`, `PreguntaNoActual`, `PreguntaYaCerrada`, `OpcionesNoMostradasTodavia` y `TiempoAgotado` (INV-AEV-08, aunque el Docente no haya cerrado la pregunta); devuelve el tiempo de respuesta medido desde `opciones_mostradas_en`. `reconstruir()` aplica `PreguntaEnVivoCerrada`
- ✅ **`ParticipacionEnVivo`** — `RespuestaEnVivo` (VO inmutable), `responder()` (INV-AEV-07, `RespuestaYaRegistrada`), `puntaje_acumulado`, `reconstruir()` con dispatch por `event_type`
- ✅ **`RespuestaEnVivoRegistrada`** (`eventos_en_vivo.py`) — evento repetible del stream de la participación; `desde_respuesta(...)`
- ✅ **Errores nuevos** (`errors.py`): `ParticipacionNoExiste`, `PreguntaNoActual`, `OpcionesNoMostradasTodavia`, `PreguntaYaCerrada`, `TiempoAgotado`, `RespuestaYaRegistrada`

### Use Cases (`src/actividad_evaluativa/use_cases/`)

- ✅ **`ResponderPreguntaEnVivoUseCase`** — corrige con `PreguntaConsultaPort.evaluar_correccion`, puntúa con `calcular_puntaje` (`US-6.2.1`), escribe las proyecciones sin `commit` y hace el `append` con `expected_sequence_number = len(eventos)`; ante `ConcurrenciaOptimistaError` llama a `descartar_pendientes()` y levanta `RespuestaYaRegistrada` (contrato de `US-6.2.3`). Publica el conteo recién después de persistir
- ✅ **`ResultadoRespuestaEnVivo`** — `es_correcta`, `puntaje`, `puntaje_acumulado` (sin ranking)

### Interface Adapters

- ✅ **`ParticipacionesEnVivoController`** — controller propio con un único use case; `SesionesEnVivoController` no cambia de firma

### Frameworks (`src/actividad_evaluativa/frameworks/`)

- ✅ **`POST /sesiones-en-vivo/{sesion_id}/responder`** (`api/sesiones_en_vivo_router.py`, rol `estudiante`) — 200 con `{es_correcta, puntaje, puntaje_acumulado}`; `SesionNoExiste`/`ParticipacionNoExiste` → 404, el resto de los rechazos de dominio → 422
- ✅ **`ResponderEnVivoRequest`** (`api/schemas.py`) — valida en el borde que `contenido` sea exactamente `{"opcion_indice": int}` o `{"valor": bool}` (422 si no)
- ✅ **Wiring** `get_participaciones_en_vivo_controller` en `dependencies.py`. Sin migración de DB

**Mensaje de broadcast** a todos los conectados, después de persistir:
`{"tipo": "conteo_respuestas_actualizado", "pregunta_actual_indice": N, "cantidad_respuestas": M}` — total, sin desglose por opción.

**Clave de la opción en el histograma:** `str(opcion_indice)` para opción múltiple; `"verdadero"`/`"falso"` para Verdadero/Falso.

---

## Tests

| Nivel | Cantidad | Resultado |
|-------|----------|-----------|
| Unitarios (`tests/unit/inc6/test_responder_pregunta_en_vivo.py`) | 26 nuevos (135 en `inc6`): validación, aggregate, evento, use case (incluida la carrera simulada) y controller | ✅ |
| Integración (`tests/integration/inc6/test_sesiones_en_vivo_responder_router.py`) | 16 nuevos: HTTP, **60 respuestas simultáneas** y **doble envío simultáneo** contra la DB real, broadcast por WebSocket a Docente y Estudiante | ✅ |
| BDD (`tests/step_defs/inc6/test_us_6_2_4_steps.py`) | 11 escenarios | ✅ |
| Suite completa | 1437 pasan, 1 falla | ⚠️ flaky preexistente ajeno |

El fallo es `tests/step_defs/inc3/test_us_3_2_1_steps.py::test_rechazo_fuera_del_período_vigente` (ventana de tiempo de ~1 s, ya documentada en `CLAUDE.md`; falla igual en `develop`).

---

## Métricas de Calidad

| Métrica | Valor | Objetivo | Estado |
|---------|-------|----------|--------|
| **Pylint** | 9.60/10 | ≥ 8.0 | ✅ |
| **Complejidad Ciclomática (máx/función)** | 9 (promedio 1.98) | ≤ 10 | ✅ |
| **Índice de Mantenibilidad (mín)** | 54.45 (promedio 85.15) | > 20 | ✅ |
| **Coverage (`src/actividad_evaluativa`)** | 100% | ≥ 95% | ✅ |
| **CodeGuard** (9 archivos, `--analysis-type full`) | 5 errors, 287 warnings | — | ✅ (ver detalle) |

**Estado General:** ✅ APROBADO (`quality/reports/inc6/US-6.2.4-quality.json`)

### Detalle de CodeGuard

| Check | Errors | Warnings | Infos |
|-------|--------|----------|-------|
| Security | 0 | 0 | 9 |
| PEP8 | 0 | 7 | 5 |
| Complexity | 0 | 0 | 9 |
| DeadCode | 1 | 186 | 0 |
| Maintainability | 0 | 0 | 9 |
| Pylint | 2 | 0 | 7 |
| Spelling | 0 | 95 | 1 |
| Types | 0 | 0 | 9 |
| UnusedImports | 2 | 0 | 7 |

- **4 de los 5 errors** son timeouts del pylint interno de CodeGuard (>5 s / >10 s), no hallazgos de código. El quinto es un **falso positivo** de `DeadCode` (`cls` de un `@classmethod` validator de pydantic). Pylint directo da 9.60/10; sus mensajes son `R0903 too-few-public-methods` (mismo patrón del resto de use cases y controllers del BC).
- Los warnings de `DeadCode` y `Spelling` son ruido preexistente del árbol.

---

## Decisiones y notas

- **Controller propio:** un solo use case en `ParticipacionesEnVivoController`, en vez de un 5.º en `SesionesEnVivoController` — evita el patrón de CRITICAL de CBO de US anteriores y no obligó a tocar los 4 tests que construyen el controller existente. El pre-push detectó CRITICAL de CBO (14/10) en `ResponderPreguntaEnVivoUseCase` — mismo patrón que `US-6.2.2`, no cubierto por los quality gates de Fase 7 — y se resolvió moviendo `_cargar`, `_corregir` y `_persistir` a funciones de módulo (DesignReviewer: 0 CRITICAL tras el fix).
- **`contenido` validado en el borde HTTP**, sin excepción de dominio nueva (la spec no la lista).
- **`PreguntaEnVivoCerrada` en `reconstruir()`** — fuera del plan: sin esto `PreguntaYaCerrada` no era verificable de punta a punta antes de `US-6.2.5`, que es quien emite el evento.
- **Escenario "Una sesión en la pregunta 2":** `AvanzarSiguientePregunta` es `US-6.2.6`; el step prepara la sesión en su pregunta actual y responde con el id de otra pregunta del set. Verifica `PreguntaNoActual`, no con el estado literal del Gherkin — conviene re-verificarlo con el flujo real en `US-6.2.9`.
- **Test de 60 respuestas:** las opciones se muestran *después* de crear y unir a los 60 estudiantes (bcrypt tarda más que el tiempo límite); si no, todas dan `TiempoAgotado`.
- **Pendiente para `US-6.2.5`:** cerrar la pregunta debe emitir `PreguntaEnVivoCerrada` (ya lo entiende `reconstruir()`) y reutilizar `PreguntaYaCerrada`.
