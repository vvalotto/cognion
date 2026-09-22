# Reporte de Implementación: US-6.3.1

## Resumen Ejecutivo

- **Historia de Usuario:** US-6.3.1 — Nombres de los Estudiantes en la sala de espera y el ranking
- **Puntos estimados:** 3
- **Tiempo real:** ~50 min (tracker, Fases 0 a 9). Detalle en `.claude/tracking/US-6.3.1-tracking.json`
- **Estado:** ✅ COMPLETADO
- **Fecha completado:** 2026-09-22
- **Aporta:** el hueco de "nombres de los Estudiantes" que la Iteración 2 (`inc6-candidatas.md`) dejó abierto — hoy solo viajaba `estudiante_id`, por HTTP y por WebSocket. Bloqueaba `US-6.3.3` y todo el frontend (`US-6.3.5` a `US-6.3.9`).

---

## Componentes Implementados

### Entities (`src/actividad_evaluativa/entities/ports/`)

- ✅ **`EstudianteConsultaPort.obtener_nombres(ids) -> dict[UUID, str]`** — una sola consulta por lote, no una por Estudiante
- ✅ **`ParticipanteResumen`/`ParticipanteEnRanking`** ganan `nombre: str = ""` (default) — los read models locales (`participantes_sesion_query_port.py`, `proyecciones_en_vivo_port.py`) no conocen nombres, así que sus adapters quedan sin tocar; la resolución real ocurre en el use case

### Use Cases (`src/actividad_evaluativa/use_cases/`)

- ✅ **`_resolucion_nombres.py`** (módulo nuevo) — `resolver_nombres()`, helper compartido: de-duplica ids, llama al puerto una vez, completa los faltantes con `"Estudiante sin nombre"` (`NOMBRE_SIN_RESOLVER`)
- ✅ **`UnirseASesionEnVivoUseCase`** — reutiliza el `EstudianteConsultaPort` que ya tenía inyectado desde `US-6.1.3`, sin sumar una 6ª dependencia; `_mensaje_participantes` arma `nombre` por participante
- ✅ **`ListarParticipantesUseCase`**, **`ObtenerRankingUseCase`**, **`CerrarPreguntaActualUseCase`**, **`FinalizarSesionEnVivoUseCase`** — suman `estudiante_consulta: EstudianteConsultaPort` como dependencia nueva; resuelven nombres con `dataclasses.replace()` antes de responder/transmitir

### Frameworks (`src/actividad_evaluativa/frameworks/`)

- ✅ **`EstudianteConsultaPortInProcess.obtener_nombres`** — `SELECT id, nombre FROM usuario WHERE id IN (...)` contra `UsuarioModel` de Identidad (`ADR-006`)
- ✅ **`ParticipanteResponse`/`RankingItemResponse`** ganan `nombre: str` — `GET .../participantes` y `GET .../ranking`
- ✅ **`dependencies.py`** — `CerrarPreguntaActualUseCase`, `FinalizarSesionEnVivoUseCase`, `ListarParticipantesUseCase`, `ObtenerRankingUseCase` reciben `EstudianteConsultaPortInProcess(session)` en el composition root

Los 3 broadcasts WebSocket (`participantes_actualizados`, `pregunta_cerrada`, `sesion_finalizada`) también ganan `nombre` por fila — mismo criterio de payload que ya usaban.

---

## Tests

| Nivel | Cantidad | Resultado |
|-------|----------|-----------|
| Unitarios | 749 en `tests/unit/` (5 tests nuevos de `resolver_nombres`, más los agregados/actualizados en los 5 archivos de use cases tocados) | ✅ |
| Integración (`test_sesiones_en_vivo_consultas_router.py`, `test_sesion_en_vivo_completa.py`) | 131 en `tests/integration/inc6/` — 2 tests nuevos de `nombre` real resuelto contra Identidad, 2 assertions preexistentes corregidas | ✅ |
| BDD (`US-6.3.1-nombres-estudiantes-sesion-en-vivo.feature` + `test_us_6_3_1_steps.py`) | 7 escenarios nuevos (73 en `tests/step_defs/inc6/`) | ✅ |
| RNF re-medido (`tests/uat/inc6/medir_rendimiento_cierre.py`) | 60 participantes, 30 cierres | ✅ **CUMPLE** — p95 = 79.09 ms (umbral 100 ms) |

Evidencia del RNF: `quality/reports/uat/inc6/rendimiento-cierre.json`.

**Nota sobre el escenario de rendimiento (BDD):** el step `se_mide_el_cierre` corre una sola repetición como smoke check (umbral generoso, 1000 ms) — confirmó ser flaky con el umbral real de 100 ms al correr después de toda la suite (carga de máquina, no del código: pasa aislado). El veredicto formal del RNF lo da el script dedicado, corrido aparte arriba, igual que hizo `US-6.2.9`.

---

## Métricas de Calidad

| Métrica | Valor | Objetivo | Estado |
|---------|-------|----------|--------|
| **Pylint** (13 archivos modificados/agregados) | 9.78/10 | ≥ 8.0 | ✅ |
| **Complejidad Ciclomática (máx/función)** | 6 (promedio 3.2) | ≤ 10 | ✅ |
| **Índice de Mantenibilidad (mín)** | 46.85 | > 20 | ✅ |
| **Coverage (`src/actividad_evaluativa`)** | 99% (1914 stmts; 100% en los 13 archivos tocados) | ≥ 95% | ✅ |
| **mypy** (`src/` completo) | 0 errores | 0 errores | ✅ |
| **CodeGuard** (13 archivos, `--analysis-type full`) | 22 errores, 271 warnings | — | ✅ (ver detalle) |
| **DesignReviewer** | se confirma en el pre-push | 0 CRITICAL | ⏳ |

**Estado General:** ✅ APROBADO (`quality/reports/inc6/US-6.3.1-quality.json`)

### Detalle de CodeGuard

| Check | Errors | Warnings | Infos |
|-------|--------|----------|-------|
| Security | 0 | 0 | 13 |
| PEP8 | 0 | 5 | 11 |
| Complexity | 0 | 0 | 13 |
| DeadCode | 17 | 209 | 0 |
| Maintainability | 0 | 0 | 13 |
| Pylint | 3 | 0 | 10 |
| Spelling | 0 | 56 | 6 |
| Types | 1 | 0 | 12 |
| UnusedImports | 1 | 0 | 12 |

- **DeadCode (17 errores):** falsos positivos de `vulture` sobre parámetros de métodos abstractos `ABC` (`EstudianteConsultaPort`, `ProyeccionesEnVivoPort`) — patrón preexistente en todos los puertos del BC, no introducido por esta US (vulture no entiende que un parámetro de una interfaz abstracta "se usa" en su implementación).
- **Pylint (3 errores) / Types (1) / UnusedImports (1):** timeouts intermitentes de la corrida interna de `codeguard` (mypy sin `--cache-dir`, 10s; pylint, 5-10s) — bug conocido y documentado en `CLAUDE.md` (`vvalotto/software_limpio#70`). Verificado aparte: `mypy src/` completo da 0 errores (encontró y corrigió 1 error real durante esta fase, ver más abajo) y `pylint` dedicado da 9.78/10 sin errores.
- Los warnings de `DeadCode`/`Spelling` son ruido preexistente del árbol (nombres en español, docstrings largos), mismo patrón que reportes anteriores del BC.

---

## Decisiones y notas

- **`nombre: str = ""` con default, no un DTO nuevo:** evita romper la frontera de los read models locales (no conocen Identidad) sin duplicar `ParticipanteResumen`/`ParticipanteEnRanking` en tipos "con nombre" separados — la resolución vive enteramente en la capa de use cases, donde corresponde.
- **Sin dependencia nueva en `UnirseASesionEnVivoUseCase`:** ya tenía `EstudianteConsultaPort` inyectado desde `US-6.1.3` — la spec pedía explícitamente no sumar el 6º parámetro que hubiera preocupado el CBO.
- **`mypy` encontró un bug real:** `dict(resultado.all())` sobre un `Sequence[Row[tuple[UUID, str]]]` no tipaba bien contra `Iterable[tuple[UUID, str]]` — corregido con un dict comprehension (`{fila.id: fila.nombre for fila in resultado}`). Ni los tests ni pylint lo habían detectado — confirma que el hook mypy dedicado (no el de CodeGuard) sigue siendo la fuente de verdad local de tipos.
- **RNF re-medido, no solo re-verificado por lectura de código:** con 60 participantes reales y 30 cierres, la consulta batch de nombres no movió el p95 de forma relevante frente a `US-6.2.9` (79.09 ms vs. el resultado de esa US).
- **Sin puertos nuevos hacia otros BCs:** solo se amplió `EstudianteConsultaPort`, ya existente.
- **Desbloquea:** `US-6.3.3` (estado completo de reconexión, también necesita nombres) y el arranque del frontend (`US-6.3.4` en adelante).
