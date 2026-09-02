# Plan de Implementación: US-3.1.2 - Docente crea una actividad de período abierto

**Patrón:** Clean Architecture BC-First (entities → use_cases → interface_adapters → frameworks)
**Producto:** cognion
**BC:** Actividad Evaluativa
**Estado:** ✅ COMPLETADO — 2026-08-26

## Métricas de Tiempo

Tracking real vía `tracker_cli.py` (`.claude/tracking/US-3.1.2-tracking.json`), sin comparación
contra estimaciones humanas (PRIN-001) — tiempo efectivo total ~18 min hasta el cierre de
Fase 7, 12/12 tareas de Fase 3 completadas.

## Lecciones Aprendidas

- ✅ Reutilizar el patrón de puerto `MateriaPort`/adapter in-process de `US-2.1.2` (Identidad→
  Banco de Preguntas) para `MateriaConsultaPort`/`PreguntaConsultaPort` (Actividad Evaluativa→
  Banco de Preguntas) evitó cualquier decisión de diseño nueva — tercera vez que se aplica el
  mismo patrón de integración entre BCs sin imports directos.
- ✅ `ListarMateriasUseCase` (`US-2.1.9`) fue la referencia exacta para contar preguntas activas
  de una materia sin ensanchar `PreguntaRepositoryPort` (resolver `Banco` vía
  `obtener_por_materia_id`, después `filtrar(banco.id).total`).
- 💡 `codeguard` señaló líneas >100 caracteres en 3 archivos nuevos (docstrings largos) — el
  límite del proyecto es 100, no 120 como sugiere el template genérico de Fase 0; corregido
  antes de cerrar Fase 7.
- ✅ Sin CRITICAL de CBO en `ActividadesController` (a diferencia del patrón repetido en
  `PreguntasController` de `US-2.1.2`/`US-2.1.5`/`US-2.1.6`) — esta US solo inyecta un use case,
  el patrón de CBO alto aparece recién cuando un controller acumula 4-5 use cases.

## Componentes a Implementar

### 1. Entities
- [x] `src/actividad_evaluativa/entities/actividad_evaluativa_periodo_abierto.py`
  - Aggregate `ActividadEvaluativaPeriodoAbierto` (dataclass): `id`, `materia_id`, `fecha_apertura`, `fecha_cierre`, `cantidad_preguntas`, `cantidad_intentos_permitidos`, `cerrada_manualmente` (default `False`)
  - Factory `crear(materia_id, fecha_apertura, fecha_cierre, cantidad_preguntas, cantidad_intentos_permitidos)` — valida INV-AE-02 (`fecha_apertura < fecha_cierre`, `PeriodoInvalido`) e INV-AE-03 (`cantidad_intentos_permitidos >= 1`, `CantidadIntentosInvalida`); genera `id` propio
  - INV-AE-01 (preguntas suficientes) no se valida acá — depende de un puerto externo, se valida en el Use Case (mismo criterio que INV-AE-04 de `US-2.1.2`: lo que requiere datos de otro BC no vive en el aggregate puro)
- [x] `src/actividad_evaluativa/entities/eventos.py` (nuevo archivo del BC)
  - `ActividadEvaluativaCreada` (frozen dataclass): `actividad_id`, `materia_id`, `fecha_apertura`, `fecha_cierre`, `cantidad_preguntas`, `cantidad_intentos_permitidos`, `ocurrido_en` (default factory `datetime.now(UTC)`) — mismo patrón que `banco_preguntas/entities/eventos.py`
- [x] `src/actividad_evaluativa/entities/errors.py` (extender el existente)
  - `PreguntasInsuficientes`, `PeriodoInvalido`, `CantidadIntentosInvalida`, `MateriaNoExiste` — mismo estilo que `ConcurrenciaOptimistaError` (guardan los datos del conflicto, arman el mensaje en `__init__`)
- [x] `src/actividad_evaluativa/entities/ports/pregunta_consulta_port.py`
  - `PreguntaConsultaPort` (ABC): `async def contar_activas_por_materia(materia_id: UUID) -> int`
- [x] `src/actividad_evaluativa/entities/ports/materia_consulta_port.py`
  - `MateriaDTO` (frozen dataclass: `id`, `nombre`) + `MateriaConsultaPort` (ABC): `async def obtener(materia_id: UUID) -> MateriaDTO | None` — mismo contrato que `identidad/entities/ports/materia_port.py`

### 2. Use Cases
- [x] `src/actividad_evaluativa/use_cases/crear_actividad_periodo_abierto.py`
  - `CrearActividadPeriodoAbiertoUseCase(materia_consulta: MateriaConsultaPort, pregunta_consulta: PreguntaConsultaPort, event_store: EventStorePort)`
  - `execute(materia_id, fecha_apertura, fecha_cierre, cantidad_preguntas, cantidad_intentos_permitidos) -> tuple[ActividadEvaluativaPeriodoAbierto, ActividadEvaluativaCreada]`
  - Orden: 1) `materia_consulta.obtener()` → `MateriaNoExiste` si `None`; 2) `pregunta_consulta.contar_activas_por_materia()` → `PreguntasInsuficientes` si `cantidad_preguntas` excede el conteo; 3) `ActividadEvaluativaPeriodoAbierto.crear(...)` (valida INV-AE-02/03); 4) arma `ActividadEvaluativaCreada`; 5) `event_store.append("ActividadEvaluativaPeriodoAbierto", actividad.id, 0, [EventoParaAlmacenar(...)])` con el payload serializado (UUID→str, datetime→isoformat)

### 3. Interface Adapters
- [x] `src/actividad_evaluativa/interface_adapters/controllers/actividades_controller.py`
  - `ActividadesController(crear_actividad: CrearActividadPeriodoAbiertoUseCase)` — método `crear_actividad(...)` delega al use case, mismo patrón que `MateriasController`
- [x] `src/actividad_evaluativa/frameworks/adapters/materia_consulta_port_in_process.py`
  - `MateriaConsultaPortInProcess(MateriaConsultaPort)` — implementa `obtener()` invocando `ObtenerMateriaUseCase` de `banco_preguntas` in-process, mismo patrón que `identidad/frameworks/adapters/materia_port_in_process.py`
- [x] `src/actividad_evaluativa/frameworks/adapters/pregunta_consulta_port_in_process.py`
  - `PreguntaConsultaPortInProcess(PreguntaConsultaPort)` — implementa `contar_activas_por_materia()` resolviendo `Banco` vía `BancoRepositoryPort.obtener_por_materia_id()` y contando con `PreguntaRepositoryPort.filtrar(banco.id).total`, mismo criterio que `ListarMateriasUseCase` (`US-2.1.9`)

### 4. Frameworks
- [x] `src/actividad_evaluativa/frameworks/api/schemas.py` (nuevo)
  - `CrearActividadRequest` (Pydantic): `materia_id`, `fecha_apertura`, `fecha_cierre`, `cantidad_preguntas`, `cantidad_intentos_permitidos`
  - `ActividadResponse`: `id`, `materia_id`, `fecha_apertura`, `fecha_cierre`, `cantidad_preguntas`, `cantidad_intentos_permitidos`, `cerrada_manualmente`
- [x] `src/actividad_evaluativa/frameworks/api/actividades_router.py` (nuevo)
  - `POST /actividades` (`dependencies=[Depends(require_docente)]`, 201) — mapea `MateriaNoExiste`→404, `PreguntasInsuficientes`/`PeriodoInvalido`/`CantidadIntentosInvalida`→422
- [x] `src/actividad_evaluativa/frameworks/dependencies.py` (extender)
  - `get_actividades_controller(session)` — arma `MateriaConsultaPortInProcess`, `PreguntaConsultaPortInProcess`, `SQLAlchemyEventStore`, el use case y el controller
  - `require_docente = require_rol([TipoPerfil.DOCENTE], get_current_user)` — mismo patrón que `banco_preguntas/frameworks/dependencies.py`

### 5. Integración
- [x] `src/app.py` — registrar `actividades_router` con `app.include_router(...)`

**Estado:** 13/13 tareas completadas
