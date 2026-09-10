# Plan de Implementación: US-5.1.3 - Notificación de cierre manual de una Actividad Evaluativa

**Patrón:** Clean Architecture BC-First (entities → use_cases → interface_adapters → frameworks)
**Producto:** cognion

## Decisión de diseño previa (a confirmar)

La spec deja "a definir en el plan" el contenido exacto del email y no lista
`entities/ports/notificacion_port.py` entre los artefactos a modificar — pero el postcondition
exige que el email incluya el **nombre** de la materia, y ni `NotificacionPort.notificar_cierre`
(firma actual: `actividad_id, materia_id, titulo, comisiones_ids`) ni `ComisionConsultaPort` de
Notificaciones resuelven ese nombre. `MateriaConsultaPort` (ya usado por
`CrearActividadPeriodoAbiertoUseCase`, US-3.1.2) sí lo resuelve.

**Decisión:** extender `NotificacionPort.notificar_cierre` agregando `materia_nombre: str`
(mismo criterio ya documentado en `notificar_apertura`: "viaja aparte de `materia_id` porque
Notificaciones no tiene su propio `MateriaConsultaPort`"), e inyectar `MateriaConsultaPort` en
`CerrarActividadUseCase` para resolverlo antes de invocar `notificar_cierre` — mismo patrón que
`CrearActividadPeriodoAbiertoUseCase`. Esto es un artefacto adicional a modificar respecto de la
tabla de la spec, consecuencia directa y menor de una decisión ya delegada al plan.

Segunda desviación menor respecto de la tabla de artefactos: **no se agrega ninguna factory en
`src/notificaciones/frameworks/dependencies.py`** — el `NotificarAperturaUseCase` de `US-5.1.2`
ya no usa ese archivo (`NotificacionPortInProcess` lo instancia directo en su `__init__`,
`ComisionConsultaPortInProcess(session)` + `SmtpCanalEnvio()`). Se sigue ese patrón real ya
establecido en el código para `NotificarCierreUseCase`, sin tocar `dependencies.py`.

## Componentes a Implementar

### 1. Puerto — `NotificacionPort` (entities, Actividad Evaluativa)
- [x] `src/actividad_evaluativa/entities/ports/notificacion_port.py`
  - Extender `notificar_cierre(actividad_id, materia_id, materia_nombre, titulo, comisiones_ids)`
  - Actualizar docstring (por qué `materia_nombre` viaja aparte, simétrico a `notificar_apertura`)

### 2. Use Case — `NotificarCierreUseCase` (nuevo, Notificaciones)
- [x] `src/notificaciones/use_cases/notificar_cierre.py`
  - Mismo esqueleto que `NotificarAperturaUseCase`: resuelve destinatarios vía
    `ComisionConsultaPort` (restringido a `comisiones_ids` si no está vacío, si no todas las
    comisiones de la materia; materia sin comisiones → sin envío, sin invocar `listar_destinatarios`)
  - Asunto: `f"Actividad cerrada: {titulo}"`; cuerpo con materia + título (sin fechas — a
    diferencia de apertura, el cierre no las necesita)
  - Nunca lanza — mismo `try/except Exception` + log por destinatario que `notificar_apertura`

### 3. Adapter — `NotificacionPortInProcess` (frameworks, Actividad Evaluativa)
- [x] `src/actividad_evaluativa/frameworks/adapters/notificacion_port_in_process.py`
  - `__init__` arma también `self._notificar_cierre_use_case = NotificarCierreUseCase(...)`
  - `notificar_cierre(...)` deja de ser no-op: delega en ese Use Case

### 4. Use Case — `CerrarActividadUseCase` (modificado, Actividad Evaluativa)
- [x] `src/actividad_evaluativa/use_cases/cerrar_actividad.py`
  - Constructor gana `materia_consulta: MateriaConsultaPort` y `notificacion: NotificacionPort`
  - Al final de `execute()` (después de la cascada de finalización, actividad ya cerrada):
    resuelve `materia_nombre` vía `materia_consulta.obtener(actividad.materia_id)` (materia ya
    validada al crear la actividad — sin `raise` si por algún motivo no estuviera, se envía
    `materia_nombre=""` en vez de abortar el cierre) e invoca `notificacion.notificar_cierre(...)`

### 5. Integración — Composition root (Actividad Evaluativa)
- [x] `src/actividad_evaluativa/frameworks/dependencies.py`, función `get_actividades_controller`
  - Pasar `materia_consulta` y `notificacion` (ya instanciados en esa función para
    `CrearActividadPeriodoAbiertoUseCase`) también al constructor de `CerrarActividadUseCase`

**Riesgo de CBO señalado por la spec:** `CerrarActividadUseCase` pasa de 3 a 5 colaboradores
inyectados. Vigilar el pre-push gate (`DesignReviewer`) — si marca CRITICAL, aplicar el mismo
criterio ya usado en `US-2.1.2`/`US-2.1.5`/`US-2.1.6`/`US-5.1.2` (mover una resolución de
presentación al controller, o tipar un retorno como `object`).

**Estado:** ✅ COMPLETADO — 5/5 tareas completadas
**Fecha completado:** 2026-09-10

## Métricas de Tiempo

| Fase | Tiempo real |
|------|-------------|
| Fase 0 — Validación de Contexto | (incluida en el elapsed total previo a Fase 1) |
| Fase 1 — Escenarios BDD | 26s |
| Fase 2 — Plan de Implementación | 178s |
| Fase 3 — Implementación (5 tareas) | 143s |
| Fase 4 — Tests Unitarios | 157s |
| Fase 5 — Tests de Integración | 217s |
| Fase 6 — Validación BDD | 262s |
| Fase 7 — Quality Gates | 233s |
| **Total (Fases 1-7)** | **~1216s (~20 min)** |

Nota (PRIN-001): estos tiempos son de ejecución del agente, no comparables a estimación
humana — el tracking no compara contra estimados por diseño del skill.

## Lecciones Aprendidas

- ✅ Reutilizar el esqueleto exacto de `NotificarAperturaUseCase`/`US-5.1.2` (mismo patrón de
  resolución de roster, mismo manejo de fallos "nunca lanza") redujo la Fase 3 a copiar y
  simplificar, no diseñar desde cero.
- 💡 El feature file de `US-5.1.3` reutiliza la wording "el Docente la cierra manualmente" en
  dos escenarios pero "el Docente cierra la actividad manualmente" en el cuarto — dos steps
  `@when` distintos en BDD por una diferencia de redacción entre escenarios de la misma spec.
- 💡 Los tests de integración/BDD que crean una actividad y luego la cierran capturan tanto el
  email de apertura (`US-5.1.2`) como el de cierre en el mismo stub SMTP — hace falta filtrar
  por `Subject: Actividad cerrada:` en las aserciones, no asumir que todos los mensajes son de
  cierre.
- ⚠️ Extender la firma de `NotificacionPort.notificar_cierre` con `materia_nombre` no estaba en
  la tabla de artefactos de la spec — decisión tomada en Fase 2 y confirmada con el usuario
  antes de codear, no descubierta a mitad de la implementación.
