# Plan de Implementación: US-3.3.2 - Docente cierra una actividad manualmente antes de tiempo

**Patrón:** Clean Architecture BC-first (entities → use_cases → interface_adapters → frameworks)
**Producto:** cognion — BC Actividad Evaluativa
**Estado:** ✅ COMPLETADO
**Fecha completado:** 2026-08-28

## Componentes a Implementar

### 1. Entities (`src/actividad_evaluativa/entities/`)

- [x] `entities/eventos.py` — agregar
  - `ActividadEvaluativaCerrada(actividad_id, ocurrido_en)` (frozen dataclass, mismo estilo que
    `PeriodoDisponibilidadModificado`)
- [x] `entities/actividad_evaluativa_periodo_abierto.py` — extender
  - `_aplicar_evento` (función de módulo) gana rama `"ActividadEvaluativaCerrada"` →
    `actividad.cerrada_manualmente = True`
  - `validar_para_cerrar() -> None` (nuevo, no muta): valida INV-AE-04b — `ActividadYaCerrada`
    si `self.cerrada_manualmente` ya es `True`. Sin otra validación (cerrar con evaluaciones
    activas es exactamente el caso de uso, INV-AE-04 no aplica acá)
  - `ActividadYaCerrada` ya existe (`entities/errors.py`, agregado en `US-3.3.1`) — no
    duplicar

### 2. Use Cases (`src/actividad_evaluativa/use_cases/`)

- [x] `use_cases/cerrar_actividad.py` (nuevo) —
  `CerrarActividadUseCase(event_store, evaluacion_activa_query, finalizar_evaluacion)`:
  - Carga el stream de la actividad (`ActividadNoExiste` si vacío), reconstruye vía
    `ActividadEvaluativaPeriodoAbierto.reconstruir(eventos)`
  - Llama `actividad.validar_para_cerrar()`, propaga `ActividadYaCerrada` tal cual
  - Emite `ActividadEvaluativaCerrada`, persiste con
    `event_store.append(AGGREGATE_TYPE, actividad_id, len(eventos), [...])`
  - Consulta `evaluacion_activa_query.listar_no_finalizadas()`, filtra por `actividad_id`
    (mismo criterio que `ModificarPeriodoDisponibilidadUseCase`, sin extender el port)
  - Por cada `Evaluacion` activa de esa actividad, invoca
    `finalizar_evaluacion.execute(evaluacion_id, actor="sistema")` — cascada síncrona, Regla 3
    del `VerificadorDeVencimientos` (`BC-actividad-evaluativa-modelo.md` §6b), no vía el job
    periódico de `US-3.2.4`
  - Devuelve la `ActividadEvaluativaPeriodoAbierto` con `cerrada_manualmente = True` (mutación
    post-persistencia, mismo orden que `ModificarPeriodoDisponibilidadUseCase`)

### 3. Interface Adapters

- [x] `interface_adapters/controllers/actividades_controller.py` — extender
  `ActividadesController.__init__` con `cerrar_actividad: CerrarActividadUseCase`, agregar
  método `cerrar_actividad(actividad_id)` que delega al Use Case

### 4. Frameworks

- [x] `frameworks/api/actividades_router.py` — agregar
  `POST /actividades/{actividad_id}/cerrar` (`Depends(require_docente)`, sin body — mismo
  patrón que `POST /evaluaciones/{id}/suspender`):
  - `ActividadNoExiste` → 404
  - `ActividadYaCerrada` → 422
  - Respuesta: `ActividadResponse` (ya existe)
- [x] `frameworks/dependencies.py` — `get_actividades_controller` arma
  `CerrarActividadUseCase(event_store, evaluacion_activa_query, FinalizarEvaluacionUseCase(event_store))`
  — `FinalizarEvaluacionUseCase` reutilizado tal cual, sin cambios

### 5. Integración

- [x] Verificar que `ModificarPeriodoDisponibilidadUseCase` (`US-3.3.1`) ya rechaza con
  `ActividadYaCerrada` una vez que `cerrada_manualmente = True` (vía `reconstruir()` +
  `validar_para_modificar_periodo`) — no requiere cambio, solo verificación end-to-end en BDD
  (escenario diferido de `US-3.3.1`)
- [x] Sin migración de base de datos — `ActividadEvaluativaCerrada` es un evento más en la
  tabla `events` existente

**Estado:** 4/4 tareas completadas

---

## Métricas de Tiempo

Tracking activo (`.claude/tracking/US-3.3.2-tracking.json`), Fases 0 a 8 con tracking real.
PRIN-001: tiempo real de ejecución del agente, no comparable contra estimación humana.

## Lecciones Aprendidas

- ✅ Reutilizar `FinalizarEvaluacionUseCase` con `actor="sistema"` (mecanismo introducido en
  `US-3.2.4`) para la cascada síncrona no requirió ningún cambio en ese Use Case — la extensión
  de firma ya prevista en `US-3.2.4` sirvió tal cual para un disparador nuevo (síncrono, no el
  job periódico).
- ✅ El escenario BDD "Modificar el período después de un cierre manual es rechazado", diferido
  de `US-3.3.1` por no poder construir su precondición todavía, se verificó de punta a punta sin
  ningún cambio de código adicional — `ModificarPeriodoDisponibilidadUseCase` ya rechazaba
  correctamente vía `reconstruir()` + `validar_para_modificar_periodo()`.
- 💡 Extraer `_a_response()` en el router (factorizando la construcción de `ActividadResponse`)
  evitó agregar una tercera copia del mismo bloque de 8 líneas y bajó una advertencia de
  duplicate-code que ya venía de `US-3.3.1`.
- ⚠️ Cierra completa la Iteración 3 del Incremento 3 (backend) — el modelo de dominio
  (`BC-actividad-evaluativa-modelo.md` §6b) queda con las Reglas 1/2/3 del
  `VerificadorDeVencimientos` implementadas sin desviaciones respecto de lo modelado.
