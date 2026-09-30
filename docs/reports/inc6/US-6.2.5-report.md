# Reporte de Implementación: US-6.2.5

## Resumen Ejecutivo

- **Historia de Usuario:** US-6.2.5 — Docente cierra la pregunta actual en vivo
- **Puntos estimados:** 5 (la spec no lo declara)
- **Tiempo real:** ~28 min (tracker; ~20 min son la suite completa con cobertura y CodeGuard en Fase 7 — PRIN-001, tiempo real de ejecución del agente, no comparable contra estimación humana)
- **Estado:** ✅ COMPLETADO
- **Fecha completado:** 2026-09-21
- **Aporta:** el cierre del ciclo de una pregunta de RF-09. El Docente cierra cuando quiere y todos los conectados reciben, en un único mensaje, la respuesta correcta, cuántos eligieron cada opción y el ranking. Es el momento del RNF de rendimiento: el cierre solo lee los read models ya acumulados.

---

## Componentes Implementados

### Entities (`src/actividad_evaluativa/entities/`)

- ✅ **`ActividadEvaluativaEnVivo.cerrar_pregunta()`** — rechaza sin mutar con `SesionNoEnCurso`, `OpcionesNoMostradasTodavia` (INV-AEV-09) o `PreguntaYaCerrada`; validación en el helper de módulo `_validar_para_cerrar` (no suma CBO a la clase). `reconstruir()` ya aplicaba `PreguntaEnVivoCerrada` desde `US-6.2.4`
- ✅ **`PreguntaEnVivoCerrada`** (`eventos_en_vivo.py`) — payload mínimo (`sesion_id`, `pregunta_actual_indice`, `pregunta_id`, `ocurrido_en`); ranking e histograma no se persisten, viven en los read models. Sin errores, puertos ni migraciones nuevos

### Use Cases (`src/actividad_evaluativa/use_cases/`)

- ✅ **`CerrarPreguntaActualUseCase`** — `load` → `reconstruir` → `cerrar_pregunta` → `append` con `expected_sequence_number = len(eventos)`; `ConcurrenciaOptimistaError` → `PreguntaYaCerrada`. Después de persistir lee `distribucion` y `ranking` (`ProyeccionesEnVivoQueryPort`) y `obtener_detalle_correccion` (`PreguntaConsultaPort`, sin puerto nuevo) y publica **un único** mensaje `pregunta_cerrada`

### Interface Adapters

- ✅ **`ConduccionEnVivoController.cerrar_pregunta`** — ya separado en el refactor `992b0ea`; queda con 2 use cases (`mostrar_opciones`, `cerrar_pregunta`)

### Frameworks (`src/actividad_evaluativa/frameworks/`)

- ✅ **`POST /sesiones-en-vivo/{sesion_id}/cerrar-pregunta`** (rol `docente`, sin body) — 200 con el estado de la sesión; `SesionNoExiste` → 404, `SesionNoEnCurso`/`OpcionesNoMostradasTodavia`/`PreguntaYaCerrada` → 422
- ✅ **Wiring** en `get_conduccion_en_vivo_controller`

**Mensaje de broadcast** a todos los conectados, después de persistir:
`{"tipo": "pregunta_cerrada", "pregunta_actual_indice": N, "respuesta_correcta": {"contenido", "texto", "opciones"}, "distribucion": [{"opcion", "cantidad"}], "ranking": [{"posicion", "estudiante_id", "puntaje_acumulado"}]}`

---

## Tests

| Nivel | Cantidad | Resultado |
|-------|----------|-----------|
| Unitarios (`test_cerrar_pregunta_actual_use_case.py`, `test_actividad_evaluativa_en_vivo.py`) | 16 nuevos (693 en `tests/unit`): entidad, evento, use case (carrera simulada incluida) y controller | ✅ |
| Integración (`test_sesiones_en_vivo_cerrar_pregunta_router.py`) | 12 nuevos: HTTP, doble cierre simultáneo contra la DB real, mensaje completo idéntico a dos WebSockets (Docente y Estudiante) | ✅ |
| BDD (`test_us_6_2_5_steps.py`) | 9 escenarios | ✅ |
| Suite completa | 1475 pasan, 0 fallan (16m25s) | ✅ |

---

## Métricas de Calidad

| Métrica | Valor | Objetivo | Estado |
|---------|-------|----------|--------|
| **Pylint** | 9.8/10 | ≥ 8.0 | ✅ |
| **Complejidad Ciclomática (máx/función)** | 7 (promedio 1.98) | ≤ 10 | ✅ |
| **Índice de Mantenibilidad (mín)** | 57.98 | > 20 | ✅ |
| **Coverage (`src/actividad_evaluativa`)** | 100% (1623 stmts) | ≥ 95% | ✅ |
| **CodeGuard** (7 archivos, `--analysis-type full`) | 3 errors, 132 warnings | — | ✅ (ver detalle) |
| **DesignReviewer** | 0 CRITICAL | 0 | ✅ |

**Estado General:** ✅ APROBADO (`quality/reports/inc6/US-6.2.5-quality.json`)

### Detalle de CodeGuard

| Check | Errors | Warnings | Infos |
|-------|--------|----------|-------|
| Security | 0 | 0 | 7 |
| PEP8 | 0 | 4 | 5 |
| Complexity | 0 | 0 | 7 |
| DeadCode | 0 | 42 | 0 |
| Maintainability | 0 | 0 | 7 |
| Pylint | 2 | 0 | 5 |
| Spelling | 0 | 86 | 1 |
| Types | 0 | 0 | 7 |
| UnusedImports | 1 | 0 | 6 |

- **Los 3 errors** son timeouts del pylint interno de CodeGuard (>10 s / >5 s), no hallazgos de código (`software_limpio#70`/`#71`). Pylint directo: `R0903 too-few-public-methods` en el use case (mismo patrón del BC) y `C0301` preexistentes en `dependencies.py`.
- Los warnings de `DeadCode` y `Spelling` son ruido preexistente del árbol.

---

## Decisiones y notas

- **Refactor previo de controllers** (`992b0ea`): `mostrar_opciones` pasó de `SesionesEnVivoController` a `ConduccionEnVivoController` antes de agregar `cerrar_pregunta`. Es la primera US de este BC donde el pre-push no detectó CRITICAL de CBO: se separó por responsabilidad desde el diseño, no como corrección posterior.
- **Respuesta correcta vía `obtener_detalle_correccion`:** el puerto existente ya devuelve texto, contenido correcto y opciones — no hizo falta un puerto nuevo hacia Banco de Preguntas.
- **Sin trabajo pesado en el cierre:** 3 lecturas + 1 broadcast. La medición formal del RNF (p95 ≤ 100 ms, 60 participantes) es `US-6.2.9`.
- **Cierre sin respuestas:** sin lógica especial; todos los participantes tienen fila en el ranking desde `US-6.1.3`.
- **Pendiente para `US-6.2.6`:** avanzar exige `pregunta_actual_cerrada = true` (INV-AEV-03) y debe reiniciar `opciones_mostradas`/`pregunta_actual_cerrada` en la siguiente pregunta.
