# Reporte de Implementación: US-6.2.6

## Resumen Ejecutivo

- **Historia de Usuario:** US-6.2.6 — Docente avanza a la siguiente pregunta
- **Puntos estimados:** 3 (la spec no lo declara)
- **Tiempo real:** 35 min (tracker; ~20 min son la suite completa con cobertura y CodeGuard en Fase 7 — PRIN-001, tiempo real de ejecución del agente, no comparable contra estimación humana). Detalle en `.claude/tracking/US-6.2.6-tracking.json`
- **Estado:** ✅ COMPLETADO
- **Fecha completado:** 2026-09-21
- **Aporta:** el cuarto paso del ciclo por pregunta de RF-09. Tras cerrar la pregunta, el Docente pasa a la siguiente con una pausa deliberada: la sesión queda en el estado inicial de la nueva pregunta (solo el enunciado, opciones ocultas, sin cerrar) y todos los conectados reciben el mismo mensaje `pregunta_presentada` que en el inicio.

---

## Componentes Implementados

### Entities (`src/actividad_evaluativa/entities/`)

- ✅ **`ActividadEvaluativaEnVivo.avanzar()`** — rechaza sin mutar con `SesionNoEnCurso`, `PreguntaActualNoCerrada` (INV-AEV-03) o `NoQuedanPreguntas`; validación en el helper de módulo `_validar_para_avanzar` (no suma CBO a la clase). `_pasar_a_pregunta` deja el estado inicial de la pregunta y lo comparten `avanzar()` y `reconstruir()` (`_aplicar_evento`), de modo que ambos caminos son idénticos
- ✅ **`SiguientePreguntaPresentada`** (`eventos_en_vivo.py`) — mismo shape que `SesionEnVivoIniciada`: `sesion_id`, `pregunta_actual_indice`, `pregunta_id`, `enunciado`, `tipo`, `ocurrido_en` (sin opciones)
- ✅ **`PreguntaActualNoCerrada`, `NoQuedanPreguntas`** (`errors.py`). Sin puertos ni migraciones nuevos

### Use Cases (`src/actividad_evaluativa/use_cases/`)

- ✅ **`AvanzarSiguientePreguntaUseCase`** — `load` → `reconstruir` → `avanzar` → `obtener_contenido` de la nueva pregunta → `append` con `expected_sequence_number = len(eventos)`; `ConcurrenciaOptimistaError` → `PreguntaActualNoCerrada` (el ganador ya dejó la pregunta nueva sin cerrar). Publica `pregunta_presentada` después de persistir
- ✅ **`pregunta_presentada.py`** (nuevo) — `payload_pregunta_presentada`, `mensaje_pregunta_presentada` y `tipo_de_pregunta`, extraídos de `iniciar_sesion_en_vivo.py` para no duplicar el armado del mensaje. El mensaje de `US-6.1.4` sale idéntico: sus tests no se tocaron

### Interface Adapters

- ✅ **`ConduccionEnVivoController.avanzar_siguiente_pregunta`** — pasa a 3 use cases (`mostrar_opciones`, `cerrar_pregunta`, `avanzar_siguiente_pregunta`)

### Frameworks (`src/actividad_evaluativa/frameworks/`)

- ✅ **`POST /sesiones-en-vivo/{sesion_id}/avanzar`** (rol `docente`, sin body) — 200 con el estado de la sesión; `SesionNoExiste` → 404, `SesionNoEnCurso`/`PreguntaActualNoCerrada`/`NoQuedanPreguntas` → 422
- ✅ **Wiring** en `get_conduccion_en_vivo_controller`

**Mensaje de broadcast** a todos los conectados, después de persistir:
`{"tipo": "pregunta_presentada", "pregunta_actual_indice": N, "pregunta": {"pregunta_id", "enunciado", "tipo"}}`

---

## Tests

| Nivel | Cantidad | Resultado |
|-------|----------|-----------|
| Unitarios (`test_avanzar_siguiente_pregunta_use_case.py`, `test_actividad_evaluativa_en_vivo.py`) | 15 nuevos (711 en `tests/unit`): entidad, evento, `reconstruir`, use case (carrera simulada incluida) y controller | ✅ |
| Integración (`test_sesiones_en_vivo_avanzar_router.py`) | 12 nuevos: HTTP, avance hasta la penúltima y rechazo en la última contra la DB real, doble avance simultáneo, mensaje idéntico a dos WebSockets (Docente y Estudiante) | ✅ |
| BDD (`test_us_6_2_6_steps.py`) | 7 escenarios | ✅ |
| Suite completa | 1511 pasan, 1 falla (15m58s) — ver nota | ✅ |

**Nota sobre el fallo:** `tests/step_defs/inc3/test_us_3_2_1_steps.py::test_rechazo_fuera_del_período_vigente` es un flake preexistente y determinístico en este entorno (ventana de ~1 s entre la creación de la actividad y el `IniciarEvaluacion` en su propio setup), ya documentado en la Iteración 3 del Incremento 3. No guarda relación con esta US.

---

## Métricas de Calidad

| Métrica | Valor | Objetivo | Estado |
|---------|-------|----------|--------|
| **Pylint** | 9.79/10 | ≥ 8.0 | ✅ |
| **Complejidad Ciclomática (máx/función)** | 7 (promedio 1.8) | ≤ 10 | ✅ |
| **Índice de Mantenibilidad (mín)** | 54.37 | > 20 | ✅ |
| **Coverage (`src/actividad_evaluativa`)** | 100% (1699 stmts) | ≥ 95% | ✅ |
| **CodeGuard** (9 archivos, `--analysis-type full`) | 2 errors, 219 warnings | — | ✅ (ver detalle) |
| **DesignReviewer** | se confirma en el pre-push | 0 CRITICAL | ⏳ |

**Estado General:** ✅ APROBADO (`quality/reports/inc6/US-6.2.6-quality.json`)

### Detalle de CodeGuard

| Check | Errors | Warnings | Infos |
|-------|--------|----------|-------|
| Security | 0 | 0 | 9 |
| PEP8 | 0 | 6 | 6 |
| Complexity | 0 | 0 | 9 |
| DeadCode | 0 | 81 | 0 |
| Maintainability | 0 | 0 | 9 |
| Pylint | 1 | 0 | 8 |
| Spelling | 0 | 132 | 0 |
| Types | 0 | 0 | 9 |
| UnusedImports | 1 | 0 | 8 |

- **Los 2 errors** son timeouts del pylint interno de CodeGuard (>10 s / >5 s), no hallazgos de código (`software_limpio#70`/`#71`). Pylint directo: `R0801 duplicate-code` entre `iniciar_sesion_en_vivo.py` y `avanzar_siguiente_pregunta.py` (mismo esqueleto load/reconstruir, patrón ya presente en el BC), `R0902`/`R0913`/`R0903` del mismo patrón que el resto del BC y `C0301` preexistentes. Las dos líneas largas propias se corrigieron.
- Los warnings de `DeadCode` (métodos de dominio "sin uso" porque los invocan los use cases) y `Spelling` son ruido preexistente del árbol.

---

## Decisiones y notas

- **Función compartida del mensaje:** la spec pedía no duplicar el armado de `pregunta_presentada`. Se extrajo a un módulo propio en vez de importar entre use cases, para que ninguno dependa del otro.
- **Carrera de dos avances:** el segundo choca con el chequeo optimista y se traduce a `PreguntaActualNoCerrada`, como dice la spec; el test de integración lo verifica con dos requests simultáneos contra la DB real (uno 200, otro 422).
- **`crear` baraja las preguntas:** los tests asignan el contenido según `sesion.preguntas`, no según el orden de creación.
- **Tests existentes tocados:** `test_cerrar_pregunta_actual_use_case.py` y `test_mostrar_opciones_en_vivo_use_case.py` solo por el constructor de `ConduccionEnVivoController` (3 use cases).
- **Pendiente para `US-6.2.7`:** finalizar admite hacerlo antes de agotar el set, sin exigir la última pregunta (decidido 2026-09-21).
