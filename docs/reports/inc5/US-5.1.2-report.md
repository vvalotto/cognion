# Reporte de Implementación: US-5.1.2

## Resumen Ejecutivo

- **Historia de Usuario:** US-5.1.2 — Notificación de apertura de una Actividad Evaluativa de
  período abierto
- **Puntos estimados:** 5 (no consignados explícitamente en la spec ni en `inc5-candidatas.md`)
- **Tiempo real:** ~24 min (suma de fases con tracking activo, Fases 0-8; PRIN-001 — tiempo
  real de ejecución del agente, no comparable contra estimación humana)
- **Estado:** ✅ COMPLETADO
- **Fecha completado:** 2026-09-10

---

## Componentes Implementados

### BC Actividad Evaluativa — dispara la notificación

- ✅ **`NotificacionPort.notificar_apertura`**
  (`src/actividad_evaluativa/entities/ports/notificacion_port.py`, extendido) — gana el
  parámetro `materia_nombre: str` (gap dejado abierto por `BC-notificaciones-modelo.md` §6,
  resuelto sin ensanchar ningún puerto de Notificaciones)
- ✅ **`NotificacionPortInProcess`**
  (`src/actividad_evaluativa/frameworks/adapters/notificacion_port_in_process.py`) — único
  punto de Actividad Evaluativa que importa `src.notificaciones`; `notificar_cierre` queda
  como no-op, cableado real diferido a `US-5.1.3`
- ✅ **`CrearActividadPeriodoAbiertoUseCase`**
  (`src/actividad_evaluativa/use_cases/crear_actividad_periodo_abierto.py`, modificado) —
  invoca `notificar_apertura(...)` al final de `execute()`, después de persistir
  `ActividadEvaluativaCreada`
- ✅ **`dependencies.py`** (`src/actividad_evaluativa/frameworks/dependencies.py`, modificado)
  — cablea `NotificacionPortInProcess(session)` en `get_actividades_controller`

### BC Notificaciones — primer Use Case de envío real

- ✅ **`NotificarAperturaUseCase`** (`src/notificaciones/use_cases/notificar_apertura.py`) —
  resuelve destinatarios (por comisión o por materia completa), arma el email en texto plano
  y envía por `CanalEnvioPort`; nunca propaga una excepción — un fallo de envío se loguea
  (`logging.warning`) y continúa con el resto del roster

---

## Métricas de Calidad

| Métrica | Valor | Umbral | Estado |
|---------|-------|--------|--------|
| Pylint (5 archivos de la US) | 9.19/10 | ≥ 8.0 | ✅ |
| Complejidad Ciclomática (máx/función) | 5 | ≤ 10 | ✅ |
| Índice de Mantenibilidad (mín) | 74.20 | > 20 | ✅ |
| Cobertura de Tests (código sujeto al gate) | 100% | ≥ 95% | ✅ |

**Estado General:** ✅ APROBADO (`quality/reports/inc5/US-5.1.2-quality.json`)

> Coverage 100% en los 3 archivos sujetos al gate (`notificacion_port.py`,
> `crear_actividad_periodo_abierto.py`, `notificar_apertura.py`). `frameworks/*`
> (`notificacion_port_in_process.py`, `dependencies.py`) está excluido del gate por
> `pyproject.toml` (mismo criterio en todo el proyecto) — cubierto por 2 tests unitarios + 4
> de integración reales contra PostgreSQL + SMTP-stub + 4 escenarios BDD. `mypy src/`
> (fuente de verdad local de tipos): sin errores nuevos.

### Detalle de CodeGuard

> Generado con `--analysis-type full`.

| Check | Errors | Warnings | Infos |
|-------|--------|----------|-------|
| Security | 0 | 0 | 5 |
| PEP8 | 0 | 1 | 4 |
| Complexity | 0 | 0 | 5 |
| DeadCode | 11 | 12 | 0 |
| Maintainability | 0 | 0 | 5 |
| Pylint | 0 | 1 | 4 |
| Spelling | 0 | 1 | 0 |
| Types | 0 | 0 | 5 |
| UnusedImports | 0 | 0 | 5 |

Fuente: `quality/reports/inc5/US-5.1.2-codeguard.json`.

Los 11 `errors` de DeadCode (`vulture`, 100% de confianza) son falsos positivos sobre los
parámetros de los dos métodos abstractos de `NotificacionPort` — mismo patrón ya documentado
en `US-5.1.1`. Los 12 `warnings` corresponden a clases/métodos consumidos vía DI/composition
root, que vulture no rastrea estáticamente. El único `warning` de PEP8 (línea 45 de
`dependencies.py`, 103/100 caracteres) es preexistente — verificado contra `develop` antes de
esta US, no introducido acá. El `warning` de Pylint (score aislado 5.56/10 solo sobre
`notificacion_port.py`) sube a 9.19/10 al medir el conjunto real de los 5 archivos — hallazgos:
`R0913`/`R0917` (7-9 parámetros, todos requeridos por el contrato del puerto), `R0903`
(too-few-public-methods, aceptado en Use Case de un solo `execute()`), `W2301`
(unnecessary-ellipsis, artefacto ya documentado de la versión de pylint del entorno). El
`warning` de Spelling (`'excede'` interpretada como palabra en inglés mal escrita) es un falso
positivo de idioma, mismo patrón aceptado en el resto del proyecto.

---

## Tests Implementados

### Tests Unitarios (7 tests nuevos — `tests/unit/inc5/` + `tests/unit/inc3/`)

- ✅ `test_notificar_apertura_use_case.py` (5 tests) — envío por comisiones restringidas, sin
  restricción (todas las comisiones de la materia), materia sin comisiones, fallo de un
  destinatario no aborta el resto, nunca propaga excepción
- ✅ `test_notificacion_port_in_process.py` (2 tests) — delega en el Use Case de
  Notificaciones, `notificar_cierre` no-op
- ✅ `test_crear_actividad_periodo_abierto_use_case.py` (1 test nuevo) — dispara
  `notificar_apertura` con los datos exactos de la actividad creada
- Actualizados: `_fakes.py` (nuevo `FakeNotificacionPort`) y
  `test_actividades_controller.py` (constructor de 4 argumentos)

### Tests de Integración (4 tests — `tests/integration/inc5/`) contra Postgres real + SMTP-stub

- ✅ `test_notificar_apertura_actividad_integration.py` — flujo HTTP real `POST /actividades`:
  actividad restringida a comisiones (3 emails), sin restricción (todas las comisiones de la
  materia), fallo de conexión SMTP no aborta la creación (201 igual), materia sin comisiones
  (0 emails)

### Escenarios BDD (4 escenarios — `tests/features/inc5/US-5.1.2-notificacion-apertura.feature`)

Mismos 4 escenarios ya redactados en la spec, ejercitados end-to-end vía
`tests/step_defs/inc5/test_us_5_1_2_steps.py` (steps síncronos con `asyncio.run`, `ADR-018`),
con el mismo patrón de servidor SMTP-stub con sockets bloqueantes de `US-5.1.1`.

**Todos los tests pasando:** ✅ 746/746 (unit + integration), 207/208 BDD (1 flake preexistente
de timing ajustado, confirmado ajeno a esta US al pasar en aislamiento) — sin regresiones.

---

## Archivos Creados/Modificados

### Código de producción
- `src/actividad_evaluativa/entities/ports/notificacion_port.py` (modificado)
- `src/actividad_evaluativa/frameworks/adapters/notificacion_port_in_process.py` (nuevo)
- `src/actividad_evaluativa/use_cases/crear_actividad_periodo_abierto.py` (modificado)
- `src/actividad_evaluativa/frameworks/dependencies.py` (modificado)
- `src/notificaciones/use_cases/notificar_apertura.py` (nuevo)

### Tests
- `tests/unit/inc5/test_notificar_apertura_use_case.py`
- `tests/unit/inc5/test_notificacion_port_in_process.py`
- `tests/unit/inc3/_fakes.py` (modificado — `FakeNotificacionPort`)
- `tests/unit/inc3/test_crear_actividad_periodo_abierto_use_case.py` (modificado)
- `tests/unit/inc3/test_actividades_controller.py` (modificado)
- `tests/integration/inc5/test_notificar_apertura_actividad_integration.py`
- `tests/features/inc5/US-5.1.2-notificacion-apertura.feature`
- `tests/step_defs/inc5/test_us_5_1_2_steps.py`

### Documentación
- `docs/plans/inc5/US-5.1.2-context.md`
- `docs/plans/inc5/US-5.1.2-plan.md`
- `docs/reports/inc5/US-5.1.2-report.md` (este archivo)
- `quality/reports/inc5/US-5.1.2-quality.json`
- `quality/reports/inc5/US-5.1.2-codeguard.json`
- `quality/reports/inc5/US-5.1.2-coverage.json`
- `CHANGELOG.md` (entrada en `[Unreleased]`)

---

## Criterios de Aceptación

- [x] Actividad creada con `comisiones_ids = [X, Y]` → se envía un email a cada estudiante de
  las comisiones X e Y
- [x] Actividad creada con `comisiones_ids = []` → se envía a todos los estudiantes de todas
  las comisiones de la materia
- [x] El email incluye título, fecha de apertura, fecha de cierre y nombre de la materia
- [x] Fallo de envío a un destinatario se loguea y no aborta el resto del roster
- [x] La respuesta HTTP de `POST /actividades` (201) es idéntica con o sin fallo de
  notificación
- [x] Ningún fallo de envío propaga una excepción hacia `CrearActividadPeriodoAbiertoUseCase`

**Todos los criterios cumplidos:** ✅

---

## Próximos Pasos

- [ ] `US-5.1.3` — notificación de cierre: cablea `NotificacionPort.notificar_cierre` en
  `CerrarActividadUseCase` (reemplaza el no-op de `NotificacionPortInProcess.notificar_cierre`)

---

## Lecciones Aprendidas

- 💡 El gap real de esta US (`materia_nombre` no viajaba en el puerto declarado por
  `US-5.1.1`) se resolvió extendiendo la firma existente en vez de crear un
  `MateriaConsultaPort` nuevo en Notificaciones — mismo criterio de "no ensanchar puertos" ya
  aplicado repetidamente en el proyecto.
- ✅ Reutilizar el patrón de stub SMTP embebido de `US-5.1.1`, adaptado a Fase 5
  (`asyncio.start_server`, un solo loop) y Fase 6 (thread con sockets bloqueantes, un loop por
  step), evitó cualquier dependencia de infraestructura externa (Mailhog) para verificar el
  envío real de principio a fin.
- ✅ El wiring de `NotificacionPortInProcess` en `dependencies.py` no rompió ningún test
  existente porque las actividades de los tests preexistentes no tienen comisiones asociadas
  a su materia — `NotificarAperturaUseCase` resuelve una lista vacía de destinatarios sin
  intentar ninguna conexión SMTP real, confirmado antes de escribir tests nuevos.

---

**Reporte generado automáticamente por Claude Code**
