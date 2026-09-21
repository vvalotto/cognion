# Reporte de Implementación: US-6.2.8

## Resumen Ejecutivo

- **Historia de Usuario:** US-6.2.8 — Consultar el estado de la sesión, sus participantes y su ranking
- **Puntos estimados:** 3 (la spec no lo declara)
- **Tiempo real:** ~28 min (tracker; ~12 min son la suite completa con cobertura y CodeGuard en Fase 7 — PRIN-001, tiempo real de ejecución del agente, no comparable contra estimación humana). Detalle en `.claude/tracking/US-6.2.8-tracking.json`
- **Estado:** ✅ COMPLETADO
- **Fecha completado:** 2026-09-21
- **Aporta:** el hueco de reconexión de RF-09. Todo el estado en vivo viaja por WebSocket como broadcast, así que un cliente que se cae o entra tarde no recibe lo anterior: ahora reconstruye su pantalla con una sola llamada HTTP. También expone la sala de espera del Docente y el ranking (al Estudiante solo cuando la sesión finalizó).

---

## Componentes Implementados

### Entities (`src/actividad_evaluativa/entities/`)

- ✅ **`RankingNoDisponible`** (`errors.py`) — un Estudiante pide el ranking con la sesión no `Finalizada` (§17 punto 10). Sin puertos, eventos ni migraciones nuevos: solo lecturas

### Use Cases (`src/actividad_evaluativa/use_cases/`)

- ✅ **`ObtenerEstadoSesionUseCase`** — `load` → `reconstruir` → arma la pregunta actual con `obtener_contenido`. Las `opciones` salen solo si `opciones_mostradas`; la `respuesta_correcta` (`{contenido, texto, opciones}`, mismo shape que el broadcast `pregunta_cerrada`) solo si `pregunta_actual_cerrada`. Con `estudiante_id` suma `ya_respondio` y `puntaje_acumulado` reconstruyendo su `ParticipacionEnVivo`; sin participación: `false`/`0`. Helpers a nivel de módulo (anti-CBO)
- ✅ **`ListarParticipantesUseCase`** — verifica que la sesión exista y delega en `ParticipantesSesionQueryPort.listar`
- ✅ **`ObtenerRankingUseCase`** — verifica existencia; si `es_estudiante` y la sesión no está `Finalizada` → `RankingNoDisponible`; lee `ProyeccionesEnVivoQueryPort.ranking`

### Interface Adapters

- ✅ **`SesionesEnVivoQueryController`** (nuevo) — separado de los controllers de comandos (command/query, mismo criterio que `ActividadesQueryController`)

### Frameworks (`src/actividad_evaluativa/frameworks/`)

- ✅ **`GET /sesiones-en-vivo/{id}`** (`docente`, `estudiante`) — el rol sale del JWT: al Estudiante le suma su avance propio; al Docente esos campos van `null`
- ✅ **`GET /sesiones-en-vivo/{id}/participantes`** (`docente`) — sala de espera en orden de unión
- ✅ **`GET /sesiones-en-vivo/{id}/ranking`** (`docente`, `estudiante`) — el Docente siempre; el Estudiante solo con la sesión `Finalizada` (403 antes)
- ✅ Schemas `EstadoSesionEnVivoResponse`, `PreguntaActualResponse`, `RespuestaCorrectaResponse`, `ParticipanteResponse`, `RankingItemResponse` y wiring `get_sesiones_en_vivo_query_controller`

`SesionNoExiste` → 404 en los tres. Ninguna consulta escribe eventos (verificado en un test de integración).

---

## Tests

| Nivel | Cantidad | Resultado |
|-------|----------|-----------|
| Unitarios (`test_consultas_sesion_en_vivo_use_case.py`) | 18 nuevos (739 en `tests/unit`): estado en cada fase de la pregunta, Verdadero/Falso, avance del Estudiante, sin participación, no escribe, participantes, ranking por rol, controller | ✅ |
| Integración (`test_sesiones_en_vivo_consultas_router.py`) | 16 nuevos: HTTP contra la DB real, los tres endpoints, roles, sin token, ranking antes/después de finalizar | ✅ |
| BDD (`test_us_6_2_8_steps.py`) | 10 escenarios | ✅ |
| Suite completa | 1586 pasan, 0 fallan (10m11s) | ✅ |

**Nota sobre el escenario "1200 puntos":** el puntaje real depende del tiempo de respuesta (500-4000), así que el step no fija 1200: verifica que `puntaje_acumulado` coincida con el que el servidor devolvió al responder y sea mayor que 0.

---

## Métricas de Calidad

| Métrica | Valor | Objetivo | Estado |
|---------|-------|----------|--------|
| **Pylint** | 9.87/10 | ≥ 8.0 | ✅ |
| **Complejidad Ciclomática (máx/función)** | 7 (promedio 1.67) | ≤ 10 | ✅ |
| **Índice de Mantenibilidad (mín)** | 46.86 | > 20 | ✅ |
| **Coverage (`src/actividad_evaluativa`)** | 100% (1873 stmts) | ≥ 95% | ✅ |
| **CodeGuard** (8 archivos, `--analysis-type full`) | 1 error, 299 warnings | — | ✅ (ver detalle) |
| **DesignReviewer** | se confirma en el pre-push | 0 CRITICAL | ⏳ |

**Estado General:** ✅ APROBADO (`quality/reports/inc6/US-6.2.8-quality.json`)

### Detalle de CodeGuard

| Check | Errors | Warnings | Infos |
|-------|--------|----------|-------|
| Security | 0 | 0 | 8 |
| PEP8 | 0 | 6 | 5 |
| Complexity | 0 | 0 | 8 |
| DeadCode | 1 | 213 | 0 |
| Maintainability | 0 | 0 | 8 |
| Pylint | 0 | 0 | 8 |
| Spelling | 0 | 80 | 1 |
| Types | 0 | 0 | 8 |
| UnusedImports | 0 | 0 | 8 |

- **El único error** es DeadCode "variable `cls` is never used" en `schemas.py:257`: un `@classmethod` de `US-6.2.4`, preexistente y no tocado por esta US.
- Pylint directo: `C0301` preexistentes y `R0903` (un método público) en los tres use cases nuevos, mismo patrón que el resto del BC. Los warnings de `DeadCode`/`Spelling` son ruido preexistente del árbol.

---

## Decisiones y notas

- **Estudiante sin participación:** el estado responde igual, con `ya_respondio = false` y `puntaje_acumulado = 0`, en vez de un error. La spec no lo define; se decidió con Víctor en el plan.
- **Sin puertos nuevos:** se reutilizaron `EventStorePort`, `PreguntaConsultaPort`, `ParticipantesSesionQueryPort` y `ProyeccionesEnVivoQueryPort`.
- **Controller de consultas propio:** evita sumar use cases al `ConduccionEnVivoController`, que ya tiene 4.
- **`opciones_mostradas_en`** se expone como propiedad de `EstadoSesion` para que el router no acceda a `estado.sesion`.
- **Pendiente para `US-6.2.9`:** la verificación E2E y del RNF de rendimiento (p95 ≤100 ms con 60 participantes); re-verificar el escenario "sesión en la pregunta 2" de `US-6.2.4`.
