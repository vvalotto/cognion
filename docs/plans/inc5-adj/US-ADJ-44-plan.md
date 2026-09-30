# Plan de Implementación: US-ADJ-44 - Docente consulta el desempeño de una Comisión completa

**Patrón:** Clean Architecture BC-first (entities → use_cases → interface_adapters → frameworks)
**Producto:** cognion (BC Analytics, con un cambio puntual en BC Actividad Evaluativa)
**Estado:** ✅ COMPLETADO — 2026-09-14
**Tiempo real (tracking):** 51 min (Fases 0 a 7), 11/11 tareas completadas
**Quality gates:** APROBADO (pylint 9.89/10, CC máx 9, MI mín 50.54, coverage 100%) —
`quality/reports/inc5-adj/US-ADJ-44-quality.json`
**Tests:** 1116/1116 (unit + integration + BDD) en verde, incluida la suite completa del
proyecto (no solo lo tocado por esta US)

## Lecciones aprendidas

- ✅ Reusar la entidad pura `ActividadEvaluativaPeriodoAbierto.reconstruir()` desde el adapter
  de Analytics (en vez de reimplementar el replay evento por evento) evitó duplicar lógica y
  dejó el adapter correcto de entrada frente a `PeriodoDisponibilidadModificado`/
  `ActividadEvaluativaCerrada` sin escribir tests de replay propios.
- ⚠️ Los fakes de test de otros archivos (`test_obtener_tasa_error_por_tema.py`,
  `test_obtener_desempeno_estudiante.py`, `test_analytics_controller.py`) rompieron al
  ampliar `EvaluacionDesempenoConsultaPort` con un método abstracto nuevo — hay que revisar
  todos los `Fake*(Port)` del BC cuando se amplía una interfaz, no solo los que toca la US
  directamente.
- 💡 Escribir los eventos BDD/integración con el payload completo y real de
  `ActividadEvaluativaCreada`/`EvaluacionIniciada` (no el payload mínimo que alcanza para leer
  solo `materia_id`) evita fallos tardíos cuando el escenario necesita reconstruir la entidad
  completa (drill-down de revisión).

## Decisión de diseño previa (a confirmar antes de codear)

`listar_actividades_abiertas` necesita el estado *actual* de `ActividadEvaluativaPeriodoAbierto`
(`fecha_cierre` puede haber cambiado por `PeriodoDisponibilidadModificado`, `US-3.3.1`;
`cerrada_manualmente` por `ActividadEvaluativaCerrada`, `US-3.3.2`) — no alcanza con leer el
primer evento del stream, como hace hoy `_materia_por_actividad` (que solo necesita
`materia_id`, invariante desde la creación).

**Decisión:** en vez de reimplementar el replay evento por evento dentro del adapter de
Analytics (duplicando `_aplicar_evento` de `actividad_evaluativa_periodo_abierto.py` y
arriesgando divergencia si ese aggregate gana un evento nuevo), el adapter va a importar y
reusar directamente `ActividadEvaluativaPeriodoAbierto.reconstruir()` — es una entidad pura de
`entities/` (dataclass sin ORM ni FastAPI), mismo criterio de excepción ya documentado para
`EventoModel` en el docstring del adapter ("Único punto de Analytics que importa código de otro
BC"). Evita duplicar lógica de replay, consistente con el criterio ya aplicado en `US-3.3.1`
("los 4 Use Case que leían `eventos[0].payload` directamente pasan a usar `reconstruir()`").

## Componentes a Implementar

### 1. BC Analytics — Port y Adapter (entities/frameworks)
- [x] `src/analytics/entities/ports/evaluacion_desempeno_consulta_port.py`
  - Agrega el método abstracto `listar_actividades_abiertas(materia_id: UUID, comision_id: UUID) -> list[UUID]`
  - Docstring: actividades con `fecha_apertura ≤ ahora ≤ fecha_cierre`, `cerrada_manualmente = False`, visibles a `comision_id` (`comisiones_ids` vacío = todas)
- [x] `src/analytics/frameworks/adapters/evaluacion_desempeno_consulta_port_in_process.py`
  - Implementa `listar_actividades_abiertas`: agrupa streams `ActividadEvaluativaPeriodoAbierto` (mismo patrón `groupby` que `_todos_los_streams_evaluacion`), filtra por `materia_id` leyendo el primer evento (barato, invariante), convierte `EventoModel` → `EventoAlmacenado` y reconstruye con `ActividadEvaluativaPeriodoAbierto.reconstruir()` solo los streams que matchean materia, aplica el filtro de fecha/cierre/comisión en memoria
  - Import nuevo: `from src.actividad_evaluativa.entities.actividad_evaluativa_periodo_abierto import ActividadEvaluativaPeriodoAbierto`
  - Import nuevo: `from src.actividad_evaluativa.entities.ports.event_store_port import EventoAlmacenado`

### 2. BC Analytics — Use Case (use_cases)
- [x] `src/analytics/use_cases/obtener_desempeno_por_comision.py` (nuevo)
  - `DesempenoComisionFila` (dataclass frozen): `estudiante_id`, `nombre`, `porcentaje_aciertos_acumulado: float | None`, `actividades_pendientes: int`
  - `ObtenerDesempenoPorComisionUseCase(comision_consulta: ComisionConsultaPort, evaluacion_desempeno_consulta: EvaluacionDesempenoConsultaPort)`
  - `execute(materia_id, comision_id)`: valida `comision_id` pertenece a `materia_id` (reusa `ComisionNoPerteneceAMateria`, mismo patrón que `ObtenerTasaErrorPorTemaUseCase._resolver_estudiante_ids`), arma una fila por estudiante del roster combinando `listar_evaluaciones_finalizadas` (por estudiante) y `listar_actividades_abiertas` (una sola vez por comisión)

### 3. BC Analytics — Controller, DI y Router (interface_adapters/frameworks)
- [x] `src/analytics/interface_adapters/controllers/analytics_controller.py`
  - Constructor gana el 3er Use Case: `obtener_desempeno_por_comision: ObtenerDesempenoPorComisionUseCase`
  - Método nuevo `obtener_desempeno_por_comision(materia_id, comision_id)`
- [x] `src/analytics/frameworks/dependencies.py`
  - `get_analytics_controller` cablea el Use Case nuevo con los puertos ya provistos
- [x] `src/analytics/frameworks/api/schemas.py`
  - `DesempenoComisionFilaResponse` (Pydantic): `estudiante_id`, `nombre`, `porcentaje_aciertos_acumulado: float | None`, `actividades_pendientes`
- [x] `src/analytics/frameworks/api/analytics_router.py`
  - `GET /materias/{materia_id}/comisiones/{comision_id}/desempeno`, rol `docente`, mapea `ComisionNoPerteneceAMateria` → 422 (mismo patrón que `obtener_tasa_error_por_tema`)

### 4. BC Actividad Evaluativa — Guard ampliado de la revisión (drill-down)
- [x] `src/actividad_evaluativa/use_cases/obtener_revision_evaluacion.py`
  - `execute(evaluacion_id, usuario_id, verificar_propietario: bool = True)` — el chequeo `evaluacion.estudiante_id != usuario_id` solo corre si `verificar_propietario` es `True`
- [x] `src/actividad_evaluativa/interface_adapters/controllers/revision_controller.py`
  - `obtener_revision(evaluacion_id, usuario_id, verificar_propietario)` — pasa el flag al Use Case
- [x] `src/actividad_evaluativa/frameworks/dependencies.py`
  - Nueva dependency `require_estudiante_o_docente = require_rol([TipoPerfil.ESTUDIANTE, TipoPerfil.DOCENTE], get_current_user)`
- [x] `src/actividad_evaluativa/frameworks/api/revision_router.py`
  - Guard: `require_estudiante` → `require_estudiante_o_docente`
  - `verificar_propietario = usuario.rol is TipoPerfil.ESTUDIANTE` (RBAC por rol, sin verificación de pertenencia Docente↔Materia — mismo precedente de `US-4.2.1`, documentado en la spec)

### 5. Integración
- [x] Ninguna integración adicional — el router de Analytics ya está montado en el `app` de FastAPI (`US-4.1.2`); el router de revisión de Actividad Evaluativa también (`US-3.2.3`). Sin nuevas dependencias externas ni configuración.

**Estado:** 0/11 tareas completadas
