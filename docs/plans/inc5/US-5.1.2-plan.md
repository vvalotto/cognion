# Plan de Implementación: US-5.1.2 - Notificación de apertura de una Actividad Evaluativa de período abierto

**Patrón:** Clean Architecture BC-first (`entities → use_cases → interface_adapters → frameworks`)
**Producto:** cognion

## Decisión de diseño previa (gap dejado abierto por `BC-notificaciones-modelo.md` §6)

El modelo de dominio deja pendiente "contenido exacto del email" para esta US, pero ni el
evento `ActividadEvaluativaCreada` ni la firma de `NotificacionPort.notificar_apertura`
(`US-5.1.1`) llevan el **nombre** de la materia — solo `materia_id` — y la postcondición de la
spec exige que el email incluya el nombre de la materia.

**Decisión:** extender la firma de `NotificacionPort.notificar_apertura(...)` con un parámetro
`materia_nombre: str`, provisto por `CrearActividadPeriodoAbiertoUseCase` a partir del
`MateriaDTO` que ya obtiene de `MateriaConsultaPort.obtener(materia_id)` al validar la
actividad — sin ensanchar ningún puerto de Notificaciones ni crear un `MateriaConsultaPort`
nuevo ahí (mismo criterio de "no ensanchar el puerto" ya aplicado repetidamente en el
proyecto, p. ej. `US-2.1.9`/`US-4.1.2`). `notificar_cierre` no se toca en esta US — su alcance
es de `US-5.1.3`.

## Componentes a Implementar

### 1. Entities (Actividad Evaluativa) — ajuste de contrato existente
- [x] `src/actividad_evaluativa/entities/ports/notificacion_port.py`
  - Agregar parámetro `materia_nombre: str` a la firma abstracta de `notificar_apertura(...)`
  - Actualizar docstring del método

### 2. Use Cases (Notificaciones)
- [x] `src/notificaciones/use_cases/notificar_apertura.py` (nuevo)
  - `NotificarAperturaUseCase` — constructor recibe `ComisionConsultaPort` y `CanalEnvioPort`
  - `execute(actividad_id, materia_id, materia_nombre, titulo, fecha_apertura, fecha_cierre, comisiones_ids)`
  - Resuelve destinatarios: si `comisiones_ids` no está vacío → `listar_destinatarios(comisiones_ids)` directo; si está vacío → `listar_comisiones_por_materia(materia_id)` y, si devuelve alguna, `listar_destinatarios(...)` sobre esas (materia sin comisiones → lista vacía, sin llamar a `listar_destinatarios`)
  - Arma asunto/cuerpo en texto plano con título, materia, fecha de apertura y fecha de cierre
  - Por cada destinatario: `try/except` alrededor de `canal_envio.enviar(...)` — captura cualquier excepción, la loguea con `logging.getLogger(__name__).warning(...)` incluyendo `estudiante_id`/`email`, y continúa con el resto del roster
  - Nunca lanza — ninguna excepción se propaga fuera de `execute()`

### 3. Frameworks (Actividad Evaluativa) — adapter e integración
- [x] `src/actividad_evaluativa/frameworks/adapters/notificacion_port_in_process.py` (nuevo)
  - `NotificacionPortInProcess(NotificacionPort)` — único punto de Actividad Evaluativa que importa `src.notificaciones`
  - Constructor recibe la `AsyncSession` compartida y arma internamente `NotificarAperturaUseCase(ComisionConsultaPortInProcess(session), SmtpCanalEnvio())`
  - `notificar_apertura(...)` delega en el Use Case de Notificaciones
  - `notificar_cierre(...)` — no-op (`pass`) en esta US; cableado real queda para `US-5.1.3` (mismo criterio de scope estrecho por US ya aplicado en el proyecto)

- [x] `src/actividad_evaluativa/use_cases/crear_actividad_periodo_abierto.py` (modificado)
  - Constructor gana el cuarto parámetro `notificacion: NotificacionPort`
  - Al final de `execute()`, después de `await self._event_store.append(...)`, invoca `await self._notificacion.notificar_apertura(actividad.id, actividad.materia_id, materia.nombre, actividad.titulo, actividad.fecha_apertura, actividad.fecha_cierre, list(actividad.comisiones_ids))`
  - Vigilar CBO al pushear (patrón de CRITICAL ya visto repetidamente) — si el pre-push gate lo detecta, resolver separando responsabilidad, mismo criterio ya aplicado en `US-2.1.2`/`2.1.5`/`2.1.6`/`3.1.3`/`3.2.1`

- [x] `src/actividad_evaluativa/frameworks/dependencies.py` (modificado)
  - `get_actividades_controller` arma `NotificacionPortInProcess(session)` y lo inyecta como cuarto argumento de `CrearActividadPeriodoAbiertoUseCase(...)`

## Validación BDD (Fase 6)

- [x] `tests/step_defs/inc5/test_us_5_1_2_steps.py` — 4/4 escenarios del `.feature` en verde.
  Suite completa de `tests/step_defs/`: 207/208 en verde, 1 fallo
  (`test_us_3_2_2_steps.py::test_suspender_no_valida_período_vigente`) confirmado como flake
  preexistente de timing ajustado (pasa en aislamiento) — mismo patrón ya documentado en
  `CLAUDE.md` para `test_rechazo_fuera_del_período_vigente`, ajeno a esta US.

## Tests de integración (Fase 5)

- [x] `tests/integration/inc5/test_notificar_apertura_actividad_integration.py` — flujo HTTP
  real `POST /actividades` con PostgreSQL real y stub SMTP local, cubre los 4 escenarios del
  `.feature`. 305/305 tests de integración en verde (sin regresiones).

## Integración
- [x] Cablear `NotificacionPortInProcess` en `get_actividades_controller` sin tocar la firma pública de `ActividadesController` ni del endpoint `POST /actividades` — la respuesta HTTP no cambia
- [x] Confirmar que un fallo de envío (excepción de `CanalEnvioPort`) no propaga hacia el endpoint — verificado en Fase 4 con un `CanalEnvioPort` fake que lanza en el primer destinatario (`tests/unit/inc5/test_notificar_apertura_use_case.py`)

**Estado:** ✅ COMPLETADO — 2026-09-10

## Métricas de Tiempo

| Fase | Real |
|------|------|
| 0 — Validación de Contexto | 25s |
| 1 — Escenarios BDD | 24s |
| 2 — Plan de Implementación | 165s |
| 3 — Implementación | 150s |
| 4 — Tests Unitarios | 167s |
| 5 — Tests de Integración | 229s |
| 6 — Validación BDD | 269s |
| 7 — Quality Gates | 373s |
| **Total** | **~24 min** |

> Sin comparación contra estimado — `PRIN-001` (`docs/rf/PLAN_v1.md`): las estimaciones de
> duración de las fases son referencias de complejidad relativa basadas en esfuerzo humano,
> no tiempos esperados de ejecución del agente.

## Lecciones aprendidas

- 💡 El gap real de esta US (materia_nombre no viajaba en el puerto declarado por `US-5.1.1`)
  se resolvió extendiendo la firma existente en vez de crear un puerto nuevo — mismo criterio
  de "no ensanchar" que el proyecto viene aplicando en otras US con gaps similares.
- ✅ Reutilizar el patrón de stub SMTP embebido (`_FakeSmtpServer`) de `US-5.1.1`, adaptado a
  Fase 5 (asyncio.start_server, un solo loop) y Fase 6 (thread con sockets bloqueantes, un
  loop por step) evitó cualquier dependencia de infraestructura externa (Mailhog) para
  verificar el envío real de principio a fin.
- ✅ El wiring de `NotificacionPortInProcess` en `dependencies.py` no rompió ningún test
  existente porque las actividades de los tests preexistentes no tienen comisiones asociadas
  a su materia — `NotificarAperturaUseCase` resuelve una lista vacía de destinatarios y no
  intenta ninguna conexión SMTP real, confirmado antes de escribir tests nuevos.

## Revisión de código obsoleto

No se detectó código obsoleto tras la implementación — solo se extendió una firma existente
(`NotificacionPort.notificar_apertura`) y se agregaron componentes nuevos, sin reemplazar
ningún archivo previo. Los fakes de `tests/unit/` que instancian
`CrearActividadPeriodoAbiertoUseCase` con la firma de 3 argumentos quedan desactualizados —no
obsoletos— y se actualizan en Fase 4 (mismo criterio de `[[feedback_fakes_unit_tests_desactualizados]]`).
