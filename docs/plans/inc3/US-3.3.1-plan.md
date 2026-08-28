# Plan de Implementación: US-3.3.1 - Docente extiende (o intenta acortar) el plazo de una actividad vigente

**Patrón:** Clean Architecture BC-first (entities → use_cases → interface_adapters → frameworks)
**Producto:** cognion — BC Actividad Evaluativa
**Estado:** ✅ COMPLETADO
**Fecha completado:** 2026-08-28

## Componentes a Implementar

### 1. Entities (`src/actividad_evaluativa/entities/`)

- [x] `entities/errors.py` — agregar
  - `NoSePuedeAcortarConEvaluacionesActivas(actividad_id)` (INV-AE-04)
  - `ActividadYaCerrada(actividad_id)` (INV-AE-04b, compartida con `US-3.3.2`)
- [x] `entities/eventos.py` — agregar
  - `PeriodoDisponibilidadModificado(actividad_id, nueva_fecha_cierre, ocurrido_en)` (frozen
    dataclass, mismo estilo que `ActividadEvaluativaCreada`)
- [x] `entities/actividad_evaluativa_periodo_abierto.py` — extender
  - `reconstruir(eventos: list[EventoAlmacenado]) -> ActividadEvaluativaPeriodoAbierto`
    (nuevo, `@staticmethod`): primer evento siempre `ActividadEvaluativaCreada` (arma campos
    base), eventos siguientes por `event_type` vía función de módulo `_aplicar_evento` (mismo
    patrón que `Evaluacion.reconstruir()`/`_aplicar_evento`, `US-3.2.2`) — por ahora solo rama
    `PeriodoDisponibilidadModificado` → `fecha_cierre` actualizada
  - `validar_para_modificar_periodo(nueva_fecha_cierre: datetime, hay_evaluaciones_activas: bool) -> None`
    (nuevo, no aggregate root; no muta, mismo criterio que `Evaluacion.validar_para_suspender()`):
    valida INV-AE-04b (`ActividadYaCerrada` si `self.cerrada_manualmente`), INV-AE-02
    (`PeriodoInvalido` si `nueva_fecha_cierre <= self.fecha_apertura`), INV-AE-04
    (`NoSePuedeAcortarConEvaluacionesActivas` si `nueva_fecha_cierre < self.fecha_cierre` y
    `hay_evaluaciones_activas`)

### 2. Use Cases (`src/actividad_evaluativa/use_cases/`)

- [x] `use_cases/modificar_periodo_disponibilidad.py` (nuevo) —
  `ModificarPeriodoDisponibilidadUseCase(event_store, evaluacion_activa_query)`:
  - Carga el stream de la actividad (`ActividadNoExiste` si vacío), reconstruye vía
    `ActividadEvaluativaPeriodoAbierto.reconstruir(eventos)`
  - Calcula `hay_evaluaciones_activas` filtrando `evaluacion_activa_query.listar_no_finalizadas()`
    por `actividad_id` (sin extender el port — el resumen ya trae `actividad_id`; contar
    localmente, no agregar un método nuevo al port para esto)
  - Llama `actividad.validar_para_modificar_periodo(...)`, propaga sus excepciones tal cual
  - Emite `PeriodoDisponibilidadModificado`, persiste con
    `event_store.append(AGGREGATE_TYPE, actividad_id, len(eventos), [...])`
  - Devuelve la `ActividadEvaluativaPeriodoAbierto` con `fecha_cierre` ya actualizada (mutación
    post-persistencia, mismo orden que `SuspenderEvaluacionUseCase`)

### 3. Ajuste de los 4 Use Case existentes que leían `eventos_actividad[0].payload` directamente

> Consecuencia obligatoria de que el stream de la actividad ahora puede tener un segundo
> evento (Decisión de diseño 2 de la spec) — sin este ajuste, un `ModificarPeriodoDisponibilidad`
> quedaría invisible para el resto del BC.

- [x] `use_cases/iniciar_evaluacion.py` — reemplazar la lectura directa de
  `eventos_actividad[0].payload` (líneas 59-62) por
  `ActividadEvaluativaPeriodoAbierto.reconstruir(eventos_actividad)` y leer
  `fecha_apertura`/`fecha_cierre`/`cantidad_preguntas` del aggregate reconstruido
- [x] `use_cases/registrar_respuesta.py` — mismo reemplazo (líneas 59-62)
- [x] `use_cases/reanudar_evaluacion.py` — mismo reemplazo (líneas 48-50)
- [x] `use_cases/verificar_vencimientos.py` — `_fecha_cierre_de()` (línea 116) reemplaza
  `eventos[0].payload["fecha_cierre"]` por `ActividadEvaluativaPeriodoAbierto.reconstruir(eventos).fecha_cierre`
  — el cacheo por corrida (`cache_fecha_cierre`) no cambia

> **Fuera de alcance de este ajuste:** ninguno de los 4 Use Case valida hoy `cerrada_manualmente`
> en su chequeo de `FueraDePeriodo` — sigue sin validarlo acá, porque `cerrada_manualmente` no
> puede ser `true` todavía (`US-3.3.2`, no implementada). Se deja para esa US, documentado en su
> propia spec.

### 4. Interface Adapters

- [x] `interface_adapters/controllers/actividades_controller.py` — extender
  `ActividadesController.__init__` con `modificar_periodo: ModificarPeriodoDisponibilidadUseCase`,
  agregar método `modificar_periodo_disponibilidad(actividad_id, nueva_fecha_cierre)` que delega
  al Use Case

### 5. Frameworks

- [x] `frameworks/api/schemas.py` — agregar `ModificarPeriodoDisponibilidadRequest(nueva_fecha_cierre: datetime)`
- [x] `frameworks/api/actividades_router.py` — agregar
  `PATCH /actividades/{actividad_id}/periodo` (`Depends(require_docente)`):
  - `ActividadNoExiste` → 404
  - `PeriodoInvalido`, `NoSePuedeAcortarConEvaluacionesActivas`, `ActividadYaCerrada` → 422
  - Respuesta: `ActividadResponse` (ya existe, incluye `fecha_cierre`/`cerrada_manualmente`)
- [x] `frameworks/dependencies.py` — `get_actividades_controller` gana
  `SQLAlchemyEvaluacionActivaQueryRepository(session)` (ya existe la clase, `US-3.2.4`) y arma
  `ModificarPeriodoDisponibilidadUseCase(event_store, evaluacion_activa_query)`

### 6. Integración

- [x] Verificar que `EventoAlmacenado`/`EventStorePort.load` no requiere cambios — ya soporta
  streams de más de un evento (usado por `Evaluacion` desde `US-3.2.1`)
- [x] No hay migración de base de datos — `PeriodoDisponibilidadModificado` es un evento más en
  la tabla `events` existente (JSONB, `US-3.1.1`), sin columna nueva

**Estado:** 6/6 tareas completadas

---

## Métricas de Tiempo

Tracking activo (`.claude/tracking/US-3.3.1-tracking.json`), Fases 0 a 8 con tracking real.
PRIN-001: tiempo real de ejecución del agente, no comparable contra estimación humana.

## Lecciones Aprendidas

- ✅ Extender la firma de `execute()` de `ActividadEvaluativaPeriodoAbierto` con `reconstruir()`
  (mismo patrón de dispatch de `Evaluacion.reconstruir()`/`_aplicar_evento`, `US-3.2.2`) permitió
  que los 4 Use Case existentes que leían `eventos[0].payload` directamente se ajustaran con un
  cambio mecánico y acotado, sin tocar ningún test previo de `US-3.1.3`/`US-3.2.1`/`US-3.2.2`/
  `US-3.2.4`.
- 💡 El escenario BDD "Modificar una actividad ya cerrada manualmente se rechaza" no pudo
  verificarse de punta a punta en esta US: su precondición (`cerrada_manualmente = true`) recién
  se puede construir cuando exista `CerrarActividad` (`US-3.3.2`). Se removió del feature de
  `US-3.3.1` (queda cubierto a nivel unitario) y se deja explícito que la verificación BDD
  end-to-end se agrega en el feature de `US-3.3.2`.
- ⚠️ La suite completa de `tests/step_defs/` reveló un test preexistente de `US-3.2.1`
  (`test_rechazo_fuera_del_período_vigente`) que falla de forma determinística en este entorno
  por una ventana de tiempo demasiado ajustada (~1s) entre la creación de la actividad y el
  `IniciarEvaluacion` vía HTTP — confirmado que no es una regresión de esta US (falla igual en
  `develop` limpio, antes de cualquier cambio). Reportado aparte, no se tocó en esta US.
