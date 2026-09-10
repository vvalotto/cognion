# Reporte de Implementación: US-5.1.1

## Resumen Ejecutivo

- **Historia de Usuario:** US-5.1.1 — Infraestructura del BC Notificaciones
- **Puntos estimados:** 5 (no consignados explícitamente en la spec ni en `inc5-candidatas.md`)
- **Tiempo real:** ~37 min (suma de fases con tracking activo, Fases 0-7; PRIN-001 — tiempo
  real de ejecución del agente, no comparable contra estimación humana)
- **Estado:** ✅ COMPLETADO
- **Fecha completado:** 2026-09-10

---

## Componentes Implementados

### BC Notificaciones — primer código del quinto BC del sistema

- ✅ **`CanalEnvioPort`** (`src/notificaciones/entities/ports/canal_envio_port.py`) — puerto
  ABC: `enviar(destinatario_email, asunto, cuerpo) -> None`
- ✅ **`DestinatarioNotificacion`** + **`ComisionConsultaPort`**
  (`src/notificaciones/entities/ports/comision_consulta_port.py`) — copia propia de
  Notificaciones hacia Identidad, con `email` (a diferencia de las copias de
  Analytics/Banco de Preguntas)
- ✅ **`SmtpCanalEnvio`** (`src/notificaciones/frameworks/adapters/smtp_canal_envio.py`) —
  `smtplib` + `asyncio.to_thread`, mismo patrón que `SmtpNotificador` de Identidad
  (`ADR-012`) — decidido con Víctor en vez de sumar `aiosmtplib` como dependencia nueva
- ✅ **`ComisionConsultaPortInProcess`**
  (`src/notificaciones/frameworks/adapters/comision_consulta_port_in_process.py`) — envuelve
  `SQLAlchemyComisionQueryRepository` de Identidad, dedupe por `estudiante_id`
- ✅ **`dependencies.py`** (`src/notificaciones/frameworks/dependencies.py`) — composition
  root inicial, sin controller/router (BC sin endpoint HTTP propio)

### BC Identidad — extensión de `ComisionQueryPort`

- ✅ **`EstudianteConEmail`** + **`listar_estudiantes_con_email`**
  (`src/identidad/entities/ports/comision_query_port.py`) — coexiste con `listar_estudiantes`
  sin reemplazarlo
- ✅ **`SQLAlchemyComisionQueryRepository.listar_estudiantes_con_email`**
  (`src/identidad/interface_adapters/gateways/comision_query_repository.py`)

### BC Actividad Evaluativa — contrato de `NotificacionPort`

- ✅ **`NotificacionPort`** (`src/actividad_evaluativa/entities/ports/notificacion_port.py`) —
  `notificar_apertura(...)`/`notificar_cierre(...)`, contrato declarado sin implementación
  cableada ni consumidor todavía — se conecta en `US-5.1.2`

---

## Métricas de Calidad

| Métrica | Valor | Umbral | Estado |
|---------|-------|--------|--------|
| Pylint (8 archivos de la US) | 8.97/10 | ≥ 8.0 | ✅ |
| Complejidad Ciclomática (máx/función) | 4 | ≤ 10 | ✅ |
| Índice de Mantenibilidad (mín) | 69.72 | > 20 | ✅ |
| Cobertura de Tests (`entities/`+`interface_adapters/`) | 93.1% | ≥ 95% | ⚠️ (ver nota) |

**Estado General:** ✅ APROBADO (`quality/reports/inc5/US-5.1.1-quality.json`)

> Coverage 93.1% es un promedio ponderado: 100% en los 4 archivos nuevos/extendidos por esta
> US (`canal_envio_port.py`, `comision_consulta_port.py`, `comision_query_port.py`,
> `notificacion_port.py`) y 100% en el método nuevo `listar_estudiantes_con_email`. El
> `82.35%` de `comision_query_repository.py` baja el promedio por 6 líneas sin cubrir en
> `tiene_comisiones_asignadas`/`tiene_comisiones_creadas` — dos métodos preexistentes
> (`US-2.2.x`/`US-ADJ-2x`) que esta US no toca, sin test de integración desde que se
> introdujeron. No es deuda nueva de `US-5.1.1` — reportado como chip aparte (`task_363ab6a5`)
> en vez de ensanchar el alcance. `frameworks/*` (`SmtpCanalEnvio`, `ComisionConsultaPortInProcess`,
> `dependencies.py`) está excluido del gate de coverage por `pyproject.toml` (mismo criterio
> en todos los BCs) — se valida vía 5 tests unitarios + 4 de integración reales contra
> PostgreSQL + 5 escenarios BDD. `mypy src/` (fuente de verdad local de tipos): `Success: no
> issues found in 235 source files`.

### Detalle de CodeGuard

> Generado con `--analysis-type full`.

| Check | Errors | Warnings | Infos |
|-------|--------|----------|-------|
| Security | 0 | 0 | 10 |
| PEP8 | 0 | 0 | 10 |
| Complexity | 0 | 0 | 10 |
| DeadCode | 21 | 34 | 2 |
| Maintainability | 0 | 0 | 10 |
| Pylint | 2 | 3 | 5 |
| Spelling | 0 | 13 | 6 |
| Types | 0 | 0 | 8 |
| UnusedImports | 0 | 0 | 10 |

Fuente: `quality/reports/inc5/US-5.1.1-codeguard.json`.

Los 21 `errors` de DeadCode (`vulture`, 100% de confianza) son falsos positivos sobre
parámetros de métodos abstractos (`CanalEnvioPort.enviar`, `ComisionConsultaPort.*`,
`ComisionQueryPort.*`, `NotificacionPort.*`) — el cuerpo es `...`, así que cada parámetro
aparece como "nunca usado". Mismo patrón ya documentado en `US-4.1.1`/`US-4.2.2`. Los 2
`errors` de Pylint son "Could not extract pylint score" sobre `__init__.py` vacíos (paquetes
nuevos), mismo patrón ya visto. Verificado con pylint directo contra los 8 archivos de la US:
8.97/10, 0 errores reales — solo `R0903` (too-few-public-methods, aceptado en Ports de un solo
método), `R0913`/`R0917` (`NotificacionPort.notificar_apertura` con 6 parámetros, todos
requeridos por el contrato modelado) y `W2301` (unnecessary-ellipsis) — este último confirmado
como artefacto de la versión de pylint del entorno sobre Ports preexistentes sin tocar (ej.
`src/analytics/entities/ports/comision_consulta_port.py`), no una regresión de esta US. Los 13
warnings de Spelling son palabras en español ('comision', 'implemente') mal interpretadas por
el diccionario en inglés de `codespell`, mismo patrón ya aceptado en el resto del proyecto.

---

## Tests Implementados

### Tests Unitarios (12 tests — `tests/unit/inc5/`)

- ✅ `test_canal_envio_port.py` (1 test) — port abstracto no instanciable
- ✅ `test_comision_consulta_port.py` (3 tests) — DTO inmutable, port abstracto no instanciable
- ✅ `test_smtp_canal_envio.py` (3 tests) — envío/asunto/destinatario/cuerpo correctos, login
  solo si hay usuario configurado, starttls+login cuando sí lo hay
- ✅ `test_comision_consulta_port_in_process.py` (4 tests) — dedupe del roster combinado,
  extracción de ids de comisiones por materia, casos vacíos, sin tocar la base de datos
- ✅ `test_notificacion_port.py` (1 test) — port abstracto no instanciable

Más el fix de dos Fakes preexistentes que dejaron de compilar al extender `ComisionQueryPort`
(`tests/unit/inc1/_fakes.py`, `tests/unit/inc4/test_comisiones_query_controller.py`).

### Tests de Integración (7 tests — `tests/integration/inc5/`) contra Postgres real

- ✅ `listar_estudiantes_con_email` incluye email, comisión sin estudiantes, no afecta a
  `listar_estudiantes` existente (3 tests)
- ✅ Roster combinado de varias comisiones sin duplicados, todas las comisiones activas de una
  materia, comisión sin estudiantes (3 tests, `ComisionConsultaPortInProcess`)
- ✅ Envío real contra un servidor SMTP-stub local con bandeja capturable (1 test)

### Escenarios BDD (5 escenarios — `tests/features/inc5/US-5.1.1-infraestructura-notificaciones.feature`)

Mismos 5 escenarios ya redactados en la spec, ejercitados end-to-end vía
`tests/step_defs/inc5/test_us_5_1_1_steps.py` (steps síncronos con `asyncio.run`, `ADR-018`).
El escenario de envío SMTP usa un servidor-stub propio con sockets bloqueantes en un thread
(no `asyncio.start_server`, que no sobrevive entre los distintos `asyncio.run()` de cada step).

**Todos los tests pasando:** ✅ 934/934 (suite `unit/` + `integration/` + `step_defs/`
completa, sin regresiones — precondición de Fase 7)

---

## Archivos Creados/Modificados

### Código de producción
- `src/notificaciones/entities/ports/canal_envio_port.py`
- `src/notificaciones/entities/ports/comision_consulta_port.py`
- `src/notificaciones/frameworks/adapters/smtp_canal_envio.py`
- `src/notificaciones/frameworks/adapters/comision_consulta_port_in_process.py`
- `src/notificaciones/frameworks/dependencies.py`
- `src/identidad/entities/ports/comision_query_port.py` (modificado)
- `src/identidad/interface_adapters/gateways/comision_query_repository.py` (modificado)
- `src/actividad_evaluativa/entities/ports/notificacion_port.py`

### Tests
- `tests/unit/inc5/test_canal_envio_port.py`
- `tests/unit/inc5/test_comision_consulta_port.py`
- `tests/unit/inc5/test_smtp_canal_envio.py`
- `tests/unit/inc5/test_comision_consulta_port_in_process.py`
- `tests/unit/inc5/test_notificacion_port.py`
- `tests/unit/inc1/_fakes.py` (modificado — `FakeComisionQueryRepository`)
- `tests/unit/inc4/test_comisiones_query_controller.py` (modificado — `_ComisionQueryPortFake`)
- `tests/integration/inc5/test_comision_query_repository_email.py`
- `tests/integration/inc5/test_comision_consulta_port_in_process.py`
- `tests/integration/inc5/test_smtp_canal_envio_integration.py`
- `tests/features/inc5/US-5.1.1-infraestructura-notificaciones.feature`
- `tests/step_defs/inc5/test_us_5_1_1_steps.py`

### Documentación
- `docs/plans/inc5/US-5.1.1-context.md`
- `docs/plans/inc5/US-5.1.1-plan.md`
- `docs/reports/inc5/US-5.1.1-report.md` (este archivo)
- `quality/reports/inc5/US-5.1.1-quality.json`
- `quality/reports/inc5/US-5.1.1-codeguard.json`
- `quality/reports/inc5/US-5.1.1-coverage.json`
- `CHANGELOG.md` (entrada en `[Unreleased]`)
- `docs/design/domain/BC-notificaciones-modelo.md` (dos "pendientes de definir" resueltos)
- `docs/architecture/03-bounded-contexts.md` (nota de los dos adaptadores SMTP actualizada)
- `pyproject.toml` (markers `edge-case`, `integration`, `US-5.1.1`)

---

## Criterios de Aceptación

- [x] `ComisionConsultaPort.listar_destinatarios([A, B])` devuelve el roster combinado sin
  duplicados si un estudiante está en más de una comisión
- [x] `ComisionConsultaPort.listar_comisiones_por_materia(materia_id)` devuelve solo las
  comisiones activas
- [x] Comisión sin inscriptos → roster vacío
- [x] `ComisionQueryPort.listar_estudiantes_con_email` expone `email` sin romper
  `listar_estudiantes` existente
- [x] `CanalEnvioPort.enviar(email, asunto, cuerpo)` (`SmtpCanalEnvio`) entrega el mensaje al
  servidor SMTP configurado — verificado contra un servidor-stub local (Mailhog real queda
  pendiente de instalación manual, decisión explícita con Víctor, no bloquea el cierre)
- [x] `NotificacionPort` declarado como interfaz en Actividad Evaluativa, sin implementación
  cableada — ningún Use Case lo invoca todavía

**Todos los criterios cumplidos:** ✅

---

## Próximos Pasos

- [ ] `US-5.1.2` — notificación de apertura: cablea `NotificacionPort` en
  `CrearActividadPeriodoAbiertoUseCase` (`NotificacionPortInProcess`)
- [ ] `US-5.1.3` — notificación de cierre: cablea `NotificacionPort` en `CerrarActividadUseCase`
- [ ] Chip pendiente (`task_363ab6a5`): tests de integración faltantes para
  `tiene_comisiones_asignadas`/`tiene_comisiones_creadas` (deuda preexistente, no de esta US)

---

## Lecciones Aprendidas

- ⚠️ La spec dejaba `aiosmtplib` como "librería candidata — a confirmar" sin haber revisado
  que ya existía un adapter SMTP funcionando en Identidad (`ADR-012`) con las mismas variables
  de entorno — decisión con Víctor en Fase 2: reusar `smtplib` + `asyncio.to_thread` en vez de
  sumar una dependencia async nueva sin caso de uso adicional que la justifique.
- ⚠️ Extender un puerto ya consumido por varios BCs (`ComisionQueryPort`) rompe cualquier Fake
  que lo implemente en `tests/unit/` sin que `mypy`/la Fase de implementación lo detecten —
  recién aparece al correr la suite completa de unit tests. Se encontraron y corrigieron dos
  Fakes (uno en `_fakes.py` compartido, otro local a un archivo de test), ninguno anticipado
  en el plan original.
- 💡 Sin Mailhog/Mailtrap instalado en este entorno, reutilizar el patrón de servidor SMTP
  embebido ya usado en `tests/integration/inc1/test_invitaciones_api_integration.py`
  (`fake_smtp_server`) evitó bloquear el cierre de la US con una instalación de
  infraestructura — extendido con una bandeja capturable para poder verificar asunto/cuerpo.

---

**Reporte generado automáticamente por Claude Code**
