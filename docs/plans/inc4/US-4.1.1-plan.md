# Plan de Implementación: US-4.1.1 - Infraestructura de consulta del BC Analytics

**Patrón:** Clean Architecture BC-first (entities → use_cases → interface_adapters → frameworks)
**Producto:** cognion
**BC:** analytics (primer código real — hoy solo el esqueleto de BL-000)

## Componentes a Implementar

### 1. Entities — Puerto y DTO de consulta
- [x] `src/analytics/entities/ports/__init__.py`
  - Paquete nuevo, no existe todavía en `src/analytics/entities/`
- [x] `src/analytics/entities/ports/evaluacion_desempeno_consulta_port.py`
  - `EvaluacionDesempenoResumen`: `dataclass(frozen=True)` con `evaluacion_id`, `actividad_id`,
    `materia_id`, `finalizada_en`, `cantidad_correctas`, `cantidad_incorrectas`
  - `EvaluacionDesempenoConsultaPort(ABC)`: `listar_evaluaciones_finalizadas(estudiante_id: UUID,
    materia_id: UUID | None) -> list[EvaluacionDesempenoResumen]` — sin conocer SQLAlchemy ni el
    event store ajeno, mismo estilo que `EvaluacionEstudianteQueryPort`
    (`src/actividad_evaluativa/entities/ports/evaluacion_estudiante_query_port.py`)

### 2. Frameworks — Adapter in-process cross-BC
- [x] `src/analytics/frameworks/adapters/__init__.py`
  - Paquete nuevo
- [x] `src/analytics/frameworks/adapters/evaluacion_desempeno_consulta_port_in_process.py`
  - `EvaluacionDesempenoConsultaPortInProcess(EvaluacionDesempenoConsultaPort)`: recibe
    `AsyncSession`, consulta directamente `EventoModel` de
    `src.actividad_evaluativa.frameworks.db.models` (único punto de Analytics que importa
    código de otro BC — mismo criterio consciente que `MateriaConsultaPortInProcess`,
    documentado en la spec)
  - Algoritmo (spec §Contexto del dominio, 4 pasos):
    1. Streams `Evaluacion` con evento `EvaluacionIniciada` cuyo `payload["estudiante_id"] ==
       estudiante_id`
    2. De esos, solo los que tienen evento `EvaluacionFinalizada` (`finalizada_en =
       occurred_at` de ese evento) — mismo criterio que
       `SQLAlchemyEvaluacionEstudianteQueryRepository.existentes_finalizadas`
    3. Por cada `evaluacion_id`, agrupar `RespuestaRegistrada` por `pregunta_id`, quedarse con
       la de `confirmada_en` más reciente (INV-AE-09) y contar `es_correcta` true/false
    4. Resolver `materia_id` leyendo el primer evento (`ActividadEvaluativaCreada`) del stream
       `ActividadEvaluativaPeriodoAbierto` de cada `actividad_id` — sin replay completo
    - Si `materia_id` viene informado en el filtro, descartar las evaluaciones cuya materia
      resuelta no coincide (antes de construir la lista final, no antes del paso 1 — necesita
      resolver `actividad_id → materia_id` igual)

### 3. Frameworks — Router base y composition root
- [x] `src/analytics/frameworks/api/__init__.py`
  - Paquete nuevo
- [x] `src/analytics/frameworks/api/analytics_router.py`
  - `router = APIRouter(prefix="/analytics", tags=["analytics"])`, sin endpoints — `US-4.1.2`
    los agrega
- [x] `src/analytics/frameworks/dependencies.py`
  - Composition root del BC, mismo patrón que
    `src/actividad_evaluativa/frameworks/dependencies.py`: `SessionDep` sobre
    `src.shared.frameworks.db.get_session`, provider
    `get_evaluacion_desempeno_consulta_port(session: SessionDep)` que instancia
    `EvaluacionDesempenoConsultaPortInProcess(session)`
  - Arranca sin controllers (no hay ninguno todavía) — `US-4.1.2` agrega el primero

### 4. Integración
- [x] `src/app.py`
  - Importar `analytics_router` y registrarlo con `app.include_router(analytics_router)`,
    después del último router de Actividad Evaluativa (mismo orden que el resto de BCs)

**Estado:** 9/9 tareas completadas — ✅ COMPLETADO

## Notas de documentación (Fase 8)

- **CHANGELOG.md:** sin cambios — se actualiza solo al cierre de Baseline (`CLAUDE.md`
  §Estructura del repositorio), no por US individual (mismo criterio que `US-3.1.1` a
  `US-ADJ-19`).
- **README / docs de arquitectura:** sin cambios — `docs/architecture/01-system-context.md`
  ya menciona Analytics a nivel conceptual (Docente consulta analytics y KPIs); esta US no
  agrega comportamiento visible al usuario, es infraestructura interna del BC.
- **Fuera de esta US:** cualquier endpoint HTTP real de Analytics (`US-4.1.2` agrega el
  primero al router base creado acá).
