# Reporte de Implementación: US-6.2.7

## Resumen Ejecutivo

- **Historia de Usuario:** US-6.2.7 — Docente finaliza la sesión — ranking final
- **Puntos estimados:** 3 (la spec no lo declara)
- **Tiempo real:** ~22 min (tracker; ~11 min son la suite completa con cobertura y CodeGuard en Fase 7 — PRIN-001, tiempo real de ejecución del agente, no comparable contra estimación humana). Detalle en `.claude/tracking/US-6.2.7-tracking.json`
- **Estado:** ✅ COMPLETADO
- **Fecha completado:** 2026-09-21
- **Aporta:** el último paso del ciclo de RF-09. El Docente da por terminada la sesión, que pasa a `Finalizada`, y todos los conectados reciben el ranking final ordenado por puntaje. Produce por API el evento `SesionEnVivoFinalizada`, que hasta ahora los tests solo sembraban a mano.

---

## Componentes Implementados

### Entities (`src/actividad_evaluativa/entities/`)

- ✅ **`ActividadEvaluativaEnVivo.finalizar()`** — rechaza sin mutar con `SesionYaFinalizada`, `SesionNoEnCurso` o `PreguntaActualNoCerrada` (INV-AEV-03), en ese orden; validación en el helper de módulo `_validar_para_finalizar`. Sin restricción de última pregunta: se puede finalizar antes de agotar el set (decidido 2026-09-21). `reconstruir()` ya aplicaba el evento (`US-6.1.3`), sin cambios
- ✅ **`SesionEnVivoFinalizada`** (`eventos_en_vivo.py`) — payload `sesion_id`, `ocurrido_en`; el ranking final no se persiste, vive en el read model. Sin errores, puertos ni migraciones nuevos

### Use Cases (`src/actividad_evaluativa/use_cases/`)

- ✅ **`FinalizarSesionEnVivoUseCase`** — `load` → `reconstruir` → `finalizar` → `append` con `expected_sequence_number = len(eventos)`; `ConcurrenciaOptimistaError` → `SesionYaFinalizada`. Después de persistir lee `ProyeccionesEnVivoQueryPort.ranking` y publica `sesion_finalizada`

### Interface Adapters

- ✅ **`ConduccionEnVivoController.finalizar_sesion`** — pasa a 4 use cases (`mostrar_opciones`, `cerrar_pregunta`, `avanzar_siguiente_pregunta`, `finalizar_sesion`)

### Frameworks (`src/actividad_evaluativa/frameworks/`)

- ✅ **`POST /sesiones-en-vivo/{sesion_id}/finalizar`** (rol `docente`, sin body) — 200 con el estado de la sesión; `SesionNoExiste` → 404, `SesionYaFinalizada`/`SesionNoEnCurso`/`PreguntaActualNoCerrada` → 422
- ✅ **Wiring** en `get_conduccion_en_vivo_controller`

**Mensaje de broadcast** a todos los conectados, después de persistir:
`{"tipo": "sesion_finalizada", "ranking": [{"posicion", "estudiante_id", "puntaje_acumulado"}]}`

---

## Tests

| Nivel | Cantidad | Resultado |
|-------|----------|-----------|
| Unitarios (`test_finalizar_sesion_en_vivo_use_case.py`) | 10 nuevos (721 en `tests/unit`): use case, orden del ranking, reconstrucción, carrera simulada, controller | ✅ |
| Integración (`test_sesiones_en_vivo_finalizar_router.py`) | 12 nuevos: HTTP, rechazos, unirse/iniciar tras finalizar, doble finalización simultánea (una 200, otra 422), mensaje idéntico a dos WebSockets | ✅ |
| BDD (`test_us_6_2_7_steps.py`) | 8 escenarios | ✅ |
| Suite completa | 1542 pasan, 0 fallan (9m11s) | ✅ |

**Limpieza de tests previos (según la spec):** la siembra de `SesionEnVivoFinalizada` en los tests de integración y BDD de `US-6.1.3`, `US-6.1.4`, `US-6.2.2`, `US-6.2.5` y `US-6.2.6` se reemplazó por el endpoint real (helpers `cerrar_pregunta_actual`, `finalizar_sesion`, `iniciar_y_finalizar`); `sembrar_evento_de_sesion` se eliminó. El fake local de los unitarios de `unirse` se mantiene porque no pasa por API.

**Nota:** el flake preexistente de `US-3.2.1` no apareció en esta corrida.

---

## Métricas de Calidad

| Métrica | Valor | Objetivo | Estado |
|---------|-------|----------|--------|
| **Pylint** | 9.79/10 | ≥ 8.0 | ✅ |
| **Complejidad Ciclomática (máx/función)** | 7 (promedio 2.08) | ≤ 10 | ✅ |
| **Índice de Mantenibilidad (mín)** | 52.94 | > 20 | ✅ |
| **Coverage (`src/actividad_evaluativa`)** | 100% (1754 stmts) | ≥ 95% | ✅ |
| **CodeGuard** (6 archivos, `--analysis-type full`) | 0 errors, 168 warnings | — | ✅ |
| **DesignReviewer** | se confirma en el pre-push | 0 CRITICAL | ⏳ |

**Estado General:** ✅ APROBADO (`quality/reports/inc6/US-6.2.7-quality.json`)

### Detalle de CodeGuard

| Check | Errors | Warnings | Infos |
|-------|--------|----------|-------|
| Security | 0 | 0 | 6 |
| PEP8 | 0 | 4 | 3 |
| Complexity | 0 | 0 | 6 |
| DeadCode | 0 | 46 | 0 |
| Maintainability | 0 | 0 | 6 |
| Pylint | 0 | 0 | 6 |
| Spelling | 0 | 118 | 0 |
| Types | 0 | 0 | 6 |
| UnusedImports | 0 | 0 | 6 |

- Pylint directo: `R0902` en `eventos_en_vivo.py` y `C0301` preexistentes, `R0903` del use case (mismo patrón que el resto del BC). La línea larga propia del docstring se corrigió.
- Los warnings de `DeadCode` (métodos de dominio "sin uso" porque los invocan los use cases) y `Spelling` son ruido preexistente del árbol.

---

## Decisiones y notas

- **Ranking sin puerto nuevo:** se reutiliza `ProyeccionesEnVivoQueryPort.ranking` (`US-6.2.3`), el mismo que el cierre de pregunta.
- **Carrera de dos finalizaciones:** la segunda choca con el chequeo optimista y se traduce a `SesionYaFinalizada`; el test de integración lo verifica con dos requests simultáneos contra la DB real.
- **CBO:** `ConduccionEnVivoController` pasa a 4 use cases; el CBO real se confirma en el pre-push. Si roza 10/10, separar antes de pushear.
- **Ranking vacío en el broadcast de integración:** el test a dos WebSockets no responde ninguna pregunta, así que verifica el mensaje con `ranking == []`; el orden por puntaje lo cubre el unitario.
- **Pendiente para `US-6.2.8`:** consultas de estado, participantes y ranking, con reconexión.
