# Reporte de Implementación: US-6.1.1

## Resumen Ejecutivo

- **Historia de Usuario:** US-6.1.1 — Infraestructura de tiempo real (WebSockets) y `ComisionConsultaPort` de Actividad Evaluativa
- **Puntos estimados:** 3
- **Tiempo real:** ~22 min (suma de fases con tracking activo; PRIN-001 — tiempo real de ejecución del agente, no comparable contra estimación humana)
- **Estado:** ✅ COMPLETADO
- **Fecha completado:** 2026-09-18

---

## Componentes Implementados

### Entities (`src/actividad_evaluativa/entities/ports/`)

- ✅ **`CanalTiempoRealPort`** (`canal_tiempo_real_port.py`) — puerto ABC con `publicar(sesion_id, mensaje)`, abstrae el broadcast en tiempo real sin que `use_cases/` conozca WebSockets
- ✅ **`ComisionConsultaPort`** (`comision_consulta_port.py`) — puerto ABC con `obtener_materia_id(comision_id)`, dirección inversa de `MateriaConsultaPort` ya existente

### Frameworks (`src/actividad_evaluativa/frameworks/`)

- ✅ **`ConnectionManager`** (`websockets/connection_manager.py`) — registro en memoria `dict[UUID, set[WebSocket]]` por sesión; `conectar`/`desconectar`/`enviar_a_sesion`, resiliente a conexiones cerradas
- ✅ **`WebSocketCanalTiempoReal`** (`websockets/websocket_canal_tiempo_real.py`) — implementa `CanalTiempoRealPort` delegando en el `ConnectionManager`
- ✅ **`ComisionConsultaPortInProcess`** (`adapters/comision_consulta_port_in_process.py`) — implementa `ComisionConsultaPort` invocando `ComisionRepositoryPort.obtener_por_id()` de Identidad in-process
- ✅ **`sesiones_en_vivo_router.py`** — router nuevo, `WS /sesiones-en-vivo/{sesion_id}/canal?token=<jwt>`: autentica por query param (verificación de JWT), acepta y registra la conexión, cierra con código `1008` si el token falta/es inválido/expiró
- ✅ **`dependencies.py`** — `ConnectionManager` singleton del proceso, `get_canal_tiempo_real()`, `get_comision_consulta_port()`
- ✅ **`src/app.py`** — registra `sesiones_en_vivo_router`

---

## Métricas de Calidad

| Métrica | Valor | Objetivo | Estado |
|---------|-------|----------|--------|
| **Pylint** | 9.41/10 | ≥ 8.0 | ✅ |
| **Complejidad Ciclomática (máx/función)** | 5 | ≤ 10 | ✅ |
| **Índice de Mantenibilidad (mín)** | 87.61 | > 20 | ✅ |
| **Coverage (`entities/ports/` nuevos)** | 100% | ≥ 95% | ✅ |
| **CodeGuard** (9 archivos analizados) | 5 errors, 43 warnings | 0 CRITICAL | ✅ |

**Estado General:** ✅ APROBADO (`quality/reports/inc6/US-6.1.1-quality.json`)

> `frameworks/` está excluido del gate de coverage por `pyproject.toml` (mismo criterio en
> todos los BCs) — se validó igual de riguroso vía 12 tests unitarios (con Fakes/dobles) + 5
> tests de integración contra la app real (`TestClient.websocket_connect`), no vía el
> porcentaje de Fase 7.

### Detalle de CodeGuard

> Generado con `--analysis-type full` (`quality/reports/inc6/US-6.1.1-codeguard.json`).

| Check | Errors | Warnings | Infos |
|-------|--------|----------|-------|
| Security | 0 | 0 | 9 |
| PEP8 | 0 | 1 | 8 |
| Complexity | 0 | 0 | 9 |
| DeadCode | 3 | 28 | 1 |
| Maintainability | 0 | 0 | 9 |
| Pylint | 2 | 0 | 7 |
| Spelling | 0 | 14 | 2 |
| Types | 0 | 0 | 8 |
| UnusedImports | 0 | 0 | 9 |

Los 3 errores de `DeadCode` y los 2 de `Pylint` son falsos positivos/limitaciones de
herramienta, no hallazgos reales — ver "Desafíos y Soluciones" abajo.

---

## Tests Implementados

### Tests Unitarios (12 tests, `tests/unit/inc6/`)

- ✅ `test_connection_manager.py` (9 tests) — conectar/aceptar handshake, broadcast a varias
  conexiones del mismo canal, aislamiento entre canales, resiliencia a conexión que falla al
  enviar, desconexión (incluye canal/conexión inexistente)
- ✅ `test_websocket_canal_tiempo_real.py` (1 test) — delega correctamente en el
  `ConnectionManager`
- ✅ `test_comision_consulta_port_in_process.py` (2 tests) — resuelve `materia_id`, `None` si
  la Comisión no existe (mismo patrón de Fake que `tests/unit/inc5/test_comision_consulta_port_in_process.py`)

**Estado:** 12/12 pasando

### Tests de Integración (5 tests, `tests/integration/inc6/`)

- ✅ `test_canal_tiempo_real.py` — dos clientes del mismo canal reciben el mismo mensaje,
  aislamiento entre sesiones, rechazo sin token (1008), rechazo con token inválido (1008),
  desconexión de un cliente no rompe el broadcast a los demás. Contra la app real
  (`TestClient(app)`, `client.portal.call(...)` para publicar en el mismo loop de eventos).

**Estado:** 5/5 pasando

### Escenarios BDD

No aplica — `skip_bdd: true`, mismo precedente que `US-3.1.1` (infra técnica). Los 6 escenarios
de `docs/specs/inc6/US-6.1.1.md` quedan cubiertos uno a uno por los tests de arriba.

**Suite completa del proyecto** (`tests/unit/` + `tests/integration/`, sin acotar): 946 passed,
sin regresiones.

---

## Archivos Creados/Modificados

### Código de Producción

- `src/actividad_evaluativa/entities/ports/canal_tiempo_real_port.py` (nuevo)
- `src/actividad_evaluativa/entities/ports/comision_consulta_port.py` (nuevo)
- `src/actividad_evaluativa/frameworks/websockets/__init__.py` (nuevo)
- `src/actividad_evaluativa/frameworks/websockets/connection_manager.py` (nuevo)
- `src/actividad_evaluativa/frameworks/websockets/websocket_canal_tiempo_real.py` (nuevo)
- `src/actividad_evaluativa/frameworks/adapters/comision_consulta_port_in_process.py` (nuevo)
- `src/actividad_evaluativa/frameworks/api/sesiones_en_vivo_router.py` (nuevo)
- `src/actividad_evaluativa/frameworks/dependencies.py` (modificado — wiring nuevo)
- `src/app.py` (modificado — registra el router nuevo)

### Tests

- `tests/unit/inc6/test_connection_manager.py` (nuevo)
- `tests/unit/inc6/test_websocket_canal_tiempo_real.py` (nuevo)
- `tests/unit/inc6/test_comision_consulta_port_in_process.py` (nuevo)
- `tests/integration/inc6/test_canal_tiempo_real.py` (nuevo)

### Documentación

- `docs/plans/US-6.1.1-context.md`
- `docs/plans/US-6.1.1-plan.md`
- `docs/reports/inc6/US-6.1.1-report.md` (este archivo)
- `quality/reports/inc6/US-6.1.1-quality.json`
- `quality/reports/inc6/US-6.1.1-codeguard.json`
- `docs/adr/ADR-005-websockets-sesiones-en-vivo.md` (nota aclaratoria — ver abajo)

---

## Desafíos y Soluciones

### Desafío 1: Autenticación sobre WebSocket

**Descripción:** El mecanismo JWT existente depende del header `Authorization: Bearer <token>`
(`HTTPBearer`), que la API nativa `WebSocket` del navegador no permite fijar en el handshake.

**Solución:** El JWT viaja como query param (`?token=...`), verificado con el mismo
`JWTIssuerPort.verificar()` ya existente — sin mecanismo de auth nuevo, solo un punto de entrada
distinto para el mismo JWT. Rechazo con código `1008` si falta/es inválido/expiró.

### Desafío 2: Testear broadcast real sin romper el loop de eventos

**Descripción:** `TestClient` (Starlette) corre la app en un thread propio con su propio loop de
eventos. Publicar un mensaje con `asyncio.run(...)` desde el thread del test crearía un loop
distinto, y los objetos `WebSocket` no son thread-safe entre loops.

**Solución:** `client.portal.call(...)` (el `BlockingPortal` que `TestClient` expone tras entrar
al `with TestClient(app) as client:`) ejecuta la corrutina en el mismo loop que las conexiones
WebSocket abiertas por ese cliente.

### Desafío 3: Falsos positivos/limitaciones de herramienta en CodeGuard

**Descripción:** `DeadCode` (vulture) marca como error "no usado" los parámetros de los métodos
abstractos nuevos (`CanalTiempoRealPort.publicar`, `ComisionConsultaPort.obtener_materia_id`).
`Pylint` reporta "Could not extract score" sobre un `__init__.py` de un solo docstring y
"execution timed out (>10s)" sobre `src/app.py`.

**Solución:** Verificado que el primero es el mismo patrón 100%-confidence ya presente y
aceptado en todos los puertos ABC existentes del proyecto (confirmado corriendo `codeguard`
sobre `materia_consulta_port.py`, ya mergeado). El segundo es el mismo tipo de timeout de
herramienta ya documentado en `CLAUDE.md` para el check de `Types`/mypy — `pylint` corrido
directamente (sin timeout) sobre los 7 archivos de código nuevo da 9.41/10. Ninguno bloquea el
gate (`should_block` implícito: son limitaciones de la herramienta, no hallazgos de código).

**Nota operativa nueva:** `codeguard` necesita `.venv/bin` en el `PATH` del proceso —
`vulture`/`codespell` están instalados en el venv del proyecto pero `codeguard` los invoca como
subprocess buscándolos en el `PATH` del shell, no en `sys.executable`. Sin ese ajuste, los 9
checks "corren" pero 2 de ellos (`DeadCode`, `Spelling`) fallan con "not installed" en vez de
analizar el código real.

---

## Cambios no Previstos

- Se agregó una nota aclaratoria a `ADR-005-websockets-sesiones-en-vivo.md`: la ADR original
  (2026-07-08) describía el flujo como si los comandos del Docente viajaran por el mismo canal
  WebSocket; el event storming del Incremento 6 (`BC-actividad-evaluativa-modelo.md`
  §12/§13/§16, 2026-09-17, posterior a la ADR) precisó que los comandos van por HTTP REST y el
  WebSocket es exclusivamente para el broadcast servidor→clientes — la decisión de usar
  WebSockets no cambia, solo se aclara el reparto. Aprobado por Víctor en esta sesión.

---

## Criterios de Aceptación

- [x] `CanalTiempoRealPort.publicar(sesion_id, mensaje)` entrega el mensaje a todas las conexiones activas de ese canal
- [x] Aislamiento entre canales — un mensaje de `sesion_id=A` nunca llega a `sesion_id=B`
- [x] `WS /sesiones-en-vivo/{sesion_id}/canal?token=<jwt>` rechaza conexión sin JWT válido (código 1008)
- [x] Desconexión de un cliente no rompe el broadcast a los demás
- [x] `ComisionConsultaPort.obtener_materia_id(comision_id)` devuelve el `materia_id` o `None` si no existe

**Estado:** 5/5 cumplidos

---

## Próximos Pasos

- [ ] `US-6.1.2` — Docente crea una sesión en vivo desde el detalle de una Comisión (usa
  `ComisionConsultaPort` de esta US)
- [ ] `US-6.1.3` — Estudiante se une a la sesión
- [ ] `US-6.1.4` — Docente inicia la sesión (primer broadcast real de un evento de dominio)

---

## Lecciones Aprendidas

- ✅ El precedente de `US-3.1.1` (`skip_bdd: true` para US técnicas de infraestructura) evitó
  generar un `.feature` que no hubiese aportado sobre lo que ya cubren los tests de
  integración/unitarios.
- ⚠️ `codeguard` necesita `.venv/bin` en el `PATH` del proceso — sin eso, `vulture`/`codespell`
  se reportan como "not installed" pese a estar instalados en el venv del proyecto.
- 💡 Testear WebSockets con `TestClient` requiere publicar vía `client.portal.call(...)`, no
  `asyncio.run(...)` desde el thread del test, para correr en el mismo loop de eventos que las
  conexiones abiertas.
- ✅ El patrón de "reemplazar el atributo privado por un Fake después de construir el adapter"
  (`tests/unit/inc5/test_comision_consulta_port_in_process.py`) se replicó sin fricción.

---

**Reporte generado automáticamente por Claude Code**
**Fecha:** 2026-09-18
