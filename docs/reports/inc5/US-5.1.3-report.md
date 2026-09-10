# Reporte de Implementación: US-5.1.3

## Resumen Ejecutivo

- **Historia de Usuario:** US-5.1.3 — Notificación de cierre manual de una Actividad
  Evaluativa de período abierto
- **Puntos estimados:** 3 (no consignados explícitamente en la spec ni en
  `inc5-candidatas.md` — asignado en el `tracker_cli.py init` de esta sesión)
- **Tiempo real:** ~26 min (suma de fases con tracking activo, Fases 1-8; PRIN-001 — tiempo
  real de ejecución del agente, no comparable contra estimación humana)
- **Estado:** ✅ COMPLETADO
- **Fecha completado:** 2026-09-10

---

## Componentes Implementados

### BC Actividad Evaluativa — dispara la notificación

- ✅ **`NotificacionPort.notificar_cierre`**
  (`src/actividad_evaluativa/entities/ports/notificacion_port.py`, extendido) — gana el
  parámetro `materia_nombre: str`, mismo criterio ya aplicado a `notificar_apertura` en
  `US-5.1.2` (Notificaciones no tiene su propio `MateriaConsultaPort`)
- ✅ **`NotificacionPortInProcess.notificar_cierre`**
  (`src/actividad_evaluativa/frameworks/adapters/notificacion_port_in_process.py`, modificado)
  — deja de ser no-op, delega en `NotificarCierreUseCase`
- ✅ **`CerrarActividadUseCase`**
  (`src/actividad_evaluativa/use_cases/cerrar_actividad.py`, modificado) — constructor gana
  `MateriaConsultaPort` y `NotificacionPort`; al final de `execute()`, después de la cascada
  de finalización, resuelve `materia_nombre` e invoca `notificar_cierre(...)`
- ✅ **`dependencies.py`** (`src/actividad_evaluativa/frameworks/dependencies.py`, modificado)
  — pasa `materia_consulta`/`notificacion` (ya instanciados para
  `CrearActividadPeriodoAbiertoUseCase`) también a `CerrarActividadUseCase`

### BC Notificaciones — segundo Use Case de envío real

- ✅ **`NotificarCierreUseCase`** (`src/notificaciones/use_cases/notificar_cierre.py`, nuevo)
  — mismo esqueleto que `NotificarAperturaUseCase` (resuelve destinatarios por comisión o por
  materia completa, envía por `CanalEnvioPort`, nunca propaga excepción), sin las fechas de
  apertura/cierre que sí lleva el email de apertura

---

## Métricas de Calidad

| Métrica | Valor | Umbral | Estado |
|---------|-------|--------|--------|
| Pylint (5 archivos de la US) | 9.47/10 | ≥ 8.0 | ✅ |
| Complejidad Ciclomática (máx/función) | 5 | ≤ 10 | ✅ |
| Índice de Mantenibilidad (mín) | 80.38 | > 20 | ✅ |
| Cobertura de Tests (código sujeto al gate) | 100% | ≥ 95% | ✅ |

**Estado General:** ✅ APROBADO (`quality/reports/inc5/US-5.1.3-quality.json`)

> Coverage 100% en los 3 archivos sujetos al gate (`notificacion_port.py`,
> `cerrar_actividad.py`, `notificar_cierre.py`). `frameworks/*`
> (`notificacion_port_in_process.py`, `dependencies.py`) está excluido del gate por
> `pyproject.toml` (mismo criterio en todo el proyecto) — cubierto por 2 tests unitarios + 4
> de integración reales contra PostgreSQL + SMTP-stub + 4 escenarios BDD. `mypy src/`
> (fuente de verdad local de tipos): sin errores — `Success: no issues found in 238 source
> files`.

### Detalle de CodeGuard

> Generado con `--analysis-type full`.

| Check | Errors | Warnings | Infos |
|-------|--------|----------|-------|
| Security | 0 | 0 | 5 |
| PEP8 | 0 | 1 | 4 |
| Complexity | 0 | 0 | 5 |
| DeadCode | 5 | 0 | 0 |
| Maintainability | 0 | 0 | 5 |
| Pylint | 0 | 2 | 3 |
| Spelling | 5 | 0 | 0 |
| Types | 2 | 0 | 3 |
| UnusedImports | 0 | 0 | 5 |

Fuente: `quality/reports/inc5/US-5.1.3-codeguard.json`.

Los 5 `errors` de DeadCode y los 5 de Spelling son fallos de herramienta no instalada en este
entorno (`vulture`/`codespell`), no hallazgos de código — mismo patrón documentado en
`US-5.1.1`/`US-5.1.2`. Los 2 `errors` de Types son el timeout de 10s de mypy dentro de
CodeGuard (bug conocido, `vvalotto/software_limpio#70`) — la fuente de verdad local (hook
dedicado de mypy) corrió sin errores. El único `warning` de PEP8 (línea 45 de
`dependencies.py`, 103/100 caracteres) es preexistente, ya señalado igual en `US-5.1.2`. Los 2
`warnings` de Pylint (score aislado 3.33/10 solo sobre `notificacion_port.py`, medido
solo-archivo) suben a 9.47/10 al medir el conjunto real de los 5 archivos — hallazgos:
`R0913`/`R0917` (7 parámetros, todos requeridos por el contrato del puerto, mismo patrón
aceptado en `US-5.1.2`), `R0903` (too-few-public-methods, aceptado en Use Case de un solo
`execute()`), `W2301` (unnecessary-ellipsis, artefacto ya documentado de la versión de pylint
del entorno), `C0301` preexistente ya mencionado.

---

## Tests Implementados

### Tests Unitarios (8 tests nuevos — `tests/unit/inc5/` + `tests/unit/inc3/`)

- ✅ `test_notificar_cierre_use_case.py` (5 tests) — envío por comisiones restringidas, sin
  restricción (todas las comisiones de la materia), materia sin comisiones, fallo de un
  destinatario no aborta el resto, nunca propaga excepción
- ✅ `test_notificacion_port_in_process.py` (reescrito) — `notificar_cierre` ahora delega en
  el Use Case de Notificaciones (antes verificaba el no-op)
- ✅ `test_cerrar_actividad_use_case.py` (2 tests nuevos) — dispara `notificar_cierre` con
  los datos exactos de la actividad cerrada; no dispara notificación adicional en el intento
  rechazado de cerrar una actividad ya cerrada
- Actualizados: `_fakes.py` (`FakeNotificacionPort.notificar_cierre` gana `materia_nombre`) y
  `test_actividades_controller.py` (constructor de 5 argumentos)

### Tests de Integración (4 tests — `tests/integration/inc5/`) contra Postgres real + SMTP-stub

- ✅ `test_notificar_cierre_actividad_integration.py` — flujo HTTP real
  `POST /actividades/{id}/cerrar`: cierre restringido a comisiones (3 emails), sin
  restricción (todas las comisiones de la materia), vencimiento natural del período (vía
  `build_verificar_vencimientos_use_case`) sin disparar ningún email, fallo de conexión SMTP
  no aborta el cierre (200 igual)

### Escenarios BDD (4 escenarios —
`tests/features/inc5/US-5.1.3-notificacion-cierre-actividad.feature`)

Mismos 4 escenarios ya redactados en la spec, ejercitados end-to-end vía
`tests/step_defs/inc5/test_us_5_1_3_steps.py` (steps síncronos con `asyncio.run`, `ADR-018`),
con el mismo patrón de servidor SMTP-stub con sockets bloqueantes de `US-5.1.1`/`US-5.1.2`.

**Todos los tests pasando:** ✅ 757/757 (unit + integration), 212/212 BDD — sin regresiones.

---

## Archivos Creados/Modificados

### Código de producción
- `src/actividad_evaluativa/entities/ports/notificacion_port.py` (modificado)
- `src/actividad_evaluativa/frameworks/adapters/notificacion_port_in_process.py` (modificado)
- `src/actividad_evaluativa/use_cases/cerrar_actividad.py` (modificado)
- `src/actividad_evaluativa/frameworks/dependencies.py` (modificado)
- `src/notificaciones/use_cases/notificar_cierre.py` (nuevo)

### Tests
- `tests/unit/inc5/test_notificar_cierre_use_case.py` (nuevo)
- `tests/unit/inc5/test_notificacion_port_in_process.py` (reescrito)
- `tests/unit/inc3/_fakes.py` (modificado — `FakeNotificacionPort.notificar_cierre`)
- `tests/unit/inc3/test_cerrar_actividad_use_case.py` (modificado + 2 tests nuevos)
- `tests/unit/inc3/test_actividades_controller.py` (modificado)
- `tests/integration/inc5/test_notificar_cierre_actividad_integration.py` (nuevo)
- `tests/features/inc5/US-5.1.3-notificacion-cierre-actividad.feature` (nuevo)
- `tests/step_defs/inc5/test_us_5_1_3_steps.py` (nuevo)

### Documentación
- `docs/plans/inc5/US-5.1.3-context.md`
- `docs/plans/inc5/US-5.1.3-plan.md`
- `docs/reports/inc5/US-5.1.3-report.md` (este archivo)
- `quality/reports/inc5/US-5.1.3-quality.json`
- `quality/reports/inc5/US-5.1.3-codeguard.json`
- `quality/reports/inc5/US-5.1.3-coverage.json`
- `docs/design/domain/BC-notificaciones-modelo.md` (corregido — tabla de `NotificacionPort`
  desactualizada desde `US-5.1.2`)
- `CHANGELOG.md` (entrada en `[Unreleased]`)

---

## Criterios de Aceptación

- [x] Cierre manual de actividad con `comisiones_ids = [X, Y]` → se envía un email a cada
  estudiante de las comisiones X e Y
- [x] Cierre manual de actividad con `comisiones_ids = []` → se envía a todos los estudiantes
  de todas las comisiones de la materia
- [x] El email de cierre incluye título y nombre de la materia
- [x] El vencimiento natural del período no dispara ningún email
- [x] El cierre en cascada de `Evaluacion`es en curso (`actor="sistema"`) no dispara ningún
  email adicional — un solo disparo por cierre de actividad
- [x] Fallo de envío a un destinatario se loguea y no aborta el resto del roster
- [x] La respuesta HTTP de `POST /actividades/{id}/cerrar` (200) es idéntica con o sin fallo
  de notificación
- [x] Ningún fallo de envío propaga una excepción hacia `CerrarActividadUseCase`

**Todos los criterios cumplidos:** ✅

---

## Decisión de diseño no listada en la spec

La spec dejaba "a definir en el plan" el contenido exacto del email de cierre, sin incluir
`entities/ports/notificacion_port.py` entre los artefactos a modificar. El postcondition exige
que el email muestre el nombre de la materia, y ni la firma original de `notificar_cierre` ni
`ComisionConsultaPort` de Notificaciones lo resuelven — se decidió en Fase 2 extender la firma
del puerto con `materia_nombre` e inyectar `MateriaConsultaPort` en `CerrarActividadUseCase`,
mismo patrón que `CrearActividadPeriodoAbiertoUseCase` (`US-5.1.2`). Confirmado con el usuario
antes de codear.

## Próximos Pasos

- [ ] Cierra completa la Iteración 1 del Incremento 5 — sin más US planificadas en esa
  iteración; el próximo paso es decidir el alcance de la Iteración 2 (o cerrar `BL-009` si
  Víctor decide que el incremento termina acá)

---

## Lecciones Aprendidas

- ✅ Reutilizar el esqueleto exacto de `NotificarAperturaUseCase` para `NotificarCierreUseCase`
  redujo la Fase 3 a copiar y simplificar (sin fechas), no diseñar desde cero.
- 💡 Los tests de integración/BDD que crean una actividad y luego la cierran capturan tanto el
  email de apertura (`US-5.1.2`) como el de cierre en el mismo stub SMTP — hubo que filtrar por
  `Subject: Actividad cerrada:` en las aserciones en vez de asumir que todos los mensajes
  capturados corresponden al cierre.
- 💡 El feature file de esta US repite la wording "el Docente la cierra manualmente" en dos
  escenarios pero usa "el Docente cierra la actividad manualmente" en el cuarto (redacción de
  la spec original) — requirió dos step definitions `@when` distintas en vez de una sola.
- ⚠️ Extender la firma de `NotificacionPort.notificar_cierre` con `materia_nombre` no estaba en
  la tabla de artefactos de la spec — se detectó y resolvió en Fase 2 (planificación), no a
  mitad de la implementación.

---

**Reporte generado automáticamente por Claude Code**
