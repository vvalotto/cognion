# Plan de Implementación: US-4.2.2 - ComisionConsultaPort — comisiones por materia y estudiantes por comisión

**Patrón:** Clean Architecture BC-first (entities → use_cases → interface_adapters → frameworks)
**Producto:** cognion
**Estado:** ✅ COMPLETADO
**Fecha completado:** 2026-09-05

## Lecciones aprendidas

- El borrador inicial del plan ubicaba el gateway SQLAlchemy en `frameworks/adapters/`
  (siguiendo la letra de `CLAUDE.md` §Arquitectura interna), pero la convención real del
  proyecto para Identidad pone los gateways en `interface_adapters/gateways/`
  (`cuenta_query_repository.py`, `comision_repository.py`) — corregido en Fase 3 antes de
  escribir el archivo. Verificar contra un archivo hermano real, no solo contra el documento,
  sigue siendo más confiable (mismo criterio que `feedback_implement_us_rutas_incN`).
- El primer intento de los BDD steps creaba comisiones con un `materia_id` aleatorio sin
  materia real detrás — pasaba en los tests unitarios/integración (que usan fakes o no separan
  esa validación) pero fallaba en BDD porque el controller sí valida existencia vía
  `MateriaPort`. Corregido creando la materia real vía `POST /materias` antes de la comisión.

## Decisiones de diseño

- **Sin Use Case nuevo** (permitido por la spec, "criterio liviano que otras queries de
  listado"): las dos consultas no tienen invariante de negocio — el controller nuevo llama
  directo al puerto de Identidad, mismo criterio ya usado en listados simples del proyecto.
- **Controller separado (`ComisionesQueryController`)**, no se extiende `ComisionesController`
  existente: separación command/query explícita desde el diseño (mismo criterio que
  `CuentaQueryPort`/`CuentasController` en `US-2.2.2`), evita mezclar los 2 comandos existentes
  (`crear_comision`, `asignar_docente`) con las 2 queries nuevas en el mismo controller.
- **Reutiliza la entidad `Comision` existente** para `listar_comisiones_por_materia` (ya tiene
  `id`/`horario`) — no hace falta un DTO nuevo del lado de Identidad. El framework mapea al
  subset `id`/`horario` recién en el `ComisionResumenResponse` de la capa HTTP.
- **`EstudianteResumen(id, nombre)`** nuevo (no `list[UUID]` plano): la spec deja la forma a
  definir según lo que necesite `US-4.2.5` — un selector de estudiante en cascada necesita
  mostrar el nombre, no solo el id, así que resolverlo acá evita un round-trip extra en
  `US-4.2.5`. Vive en `comision_query_port.py`, mismo archivo que el puerto.
- **Existencia de `materia_id`/`comision_id` se valida en el controller**, no en el puerto de
  query: `MateriaPort.obtener()` (ya existe, usado por `CrearComisionUseCase`) y
  `ComisionRepositoryPort.obtener_por_id()` (ya existe) — sin duplicar ese chequeo en
  `ComisionQueryPort`.
- **Router nuevo para el prefijo `/materias`** (`materias_comisiones_router.py`): el prefijo
  `/materias` ya lo usa `banco_preguntas/frameworks/api/materias_router.py` (POST/GET
  `/materias`) — sin colisión de path+método, pero el alias de import en `app.py` debe ser
  distinto (`identidad_materias_comisiones_router`) para no pisar el existente.
- **Analytics define su propio `ComisionConsultaPort`** con DTOs propios (`ComisionResumen`,
  `EstudianteResumen` — copias, no las clases de Identidad), mismo patrón que
  `EvaluacionDesempenoConsultaPort`/`EvaluacionDesempenoResumen`. El adapter in-process
  instancia `SQLAlchemyComisionQueryRepository` de Identidad directamente (único punto de
  Analytics que importa `src.identidad`, mismo patrón que `EstudianteConsultaPortInProcess`).
- **Sin cableado en ningún controller de Analytics todavía**: `US-4.2.4` es quien consume este
  puerto — acá solo se prueba que el mecanismo de lectura funciona (mismo criterio que
  `US-4.1.1` con `EvaluacionDesempenoConsultaPort`).

## Componentes a Implementar

### 1. Identidad — Entities

- [x] `src/identidad/entities/ports/comision_query_port.py`
  - `EstudianteResumen` (frozen dataclass: `id: UUID`, `nombre: str`)
  - `ComisionQueryPort(ABC)`:
    - `listar_comisiones_por_materia(materia_id: UUID) -> list[Comision]`
    - `listar_estudiantes(comision_id: UUID) -> list[EstudianteResumen]`

### 2. Identidad — Interface Adapters (persistencia)

> Corrección durante Fase 3: la convención real del proyecto ubica los gateways SQLAlchemy en
> `interface_adapters/gateways/` (`cuenta_query_repository.py`, `comision_repository.py`,
> `usuario_repository.py`), no en `frameworks/adapters/` como decía el borrador inicial del
> plan — corregido antes de escribir el archivo.

- [x] `src/identidad/interface_adapters/gateways/comision_query_repository.py`
  - `SQLAlchemyComisionQueryRepository(ComisionQueryPort)`
  - `listar_comisiones_por_materia`: `select(ComisionModel).where(materia_id=...)`, mapea a
    `Comision` (reutiliza el mismo mapeo campo a campo que `SQLAlchemyComisionRepository`, sin
    tocar ese archivo)
  - `listar_estudiantes`: `select(UsuarioModel).join(EstudianteModel).where(comision_id=...)`,
    mapea a `EstudianteResumen(id, nombre)`

### 3. Identidad — Interface Adapters

- [x] `src/identidad/interface_adapters/controllers/comisiones_query_controller.py`
  - `ComisionesQueryController(comision_query: ComisionQueryPort, materia_port: MateriaPort, comision_repository: ComisionRepositoryPort)`
  - `listar_comisiones_por_materia(materia_id)`: si `materia_port.obtener(materia_id)` es
    `None` → `raise MateriaNoExiste(materia_id)`; si no, delega en `comision_query`
  - `listar_estudiantes(comision_id)`: si `comision_repository.obtener_por_id(comision_id)` es
    `None` → `raise ComisionNoExiste(comision_id)`; si no, delega en `comision_query`

### 4. Identidad — Frameworks (API)

- [x] `src/identidad/frameworks/api/schemas.py` — agregar:
  - `ComisionResumenResponse(id: UUID, horario: str)`
  - `EstudianteResumenResponse(id: UUID, nombre: str)`
- [x] `src/identidad/frameworks/api/materias_comisiones_router.py` (nuevo)
  - `router = APIRouter(prefix="/materias", tags=["identidad"])`
  - `GET /{materia_id}/comisiones` (rol `docente`) → 200 `list[ComisionResumenResponse]` / 404
    si `MateriaNoExiste`
- [x] `src/identidad/frameworks/api/comisiones_router.py` (extender)
  - `GET /{comision_id}/estudiantes` (rol `docente`) → 200 `list[EstudianteResumenResponse]` /
    404 si `ComisionNoExiste`
- [x] `src/identidad/frameworks/dependencies.py`
  - `get_comisiones_query_controller(session)` — arma `SQLAlchemyComisionQueryRepository`,
    `MateriaPortInProcess`, `SQLAlchemyComisionRepository`

### 5. Identidad — Integración

- [x] `src/app.py`
  - Importar el nuevo router como
    `from src.identidad.frameworks.api.materias_comisiones_router import router as identidad_materias_comisiones_router`
  - `app.include_router(identidad_materias_comisiones_router)` — verificado sin colisión de
    paths vía `TestClient(app).get("/openapi.json")`

### 6. Analytics — Entities

- [x] `src/analytics/entities/ports/comision_consulta_port.py` (nuevo)
  - `ComisionResumen` (frozen dataclass: `id: UUID`, `horario: str`)
  - `EstudianteResumen` (frozen dataclass: `id: UUID`, `nombre: str`) — copia propia, no la de
    Identidad
  - `ComisionConsultaPort(ABC)`: mismos dos métodos que el puerto de Identidad, devolviendo los
    DTOs propios de Analytics

### 7. Analytics — Frameworks

- [x] `src/analytics/frameworks/adapters/comision_consulta_port_in_process.py` (nuevo)
  - `ComisionConsultaPortInProcess(ComisionConsultaPort)` — instancia
    `SQLAlchemyComisionQueryRepository` de Identidad con la sesión compartida, mapea `Comision`/
    `EstudianteResumen` de Identidad a los DTOs propios de Analytics
- [x] `src/analytics/frameworks/dependencies.py`
  - `get_comision_consulta_port(session) -> ComisionConsultaPort` — provider nuevo, sin
    consumidor todavía (lo cablea `US-4.2.4`)

**Estado:** 7/7 tareas completadas

## Tests

- Unitarios: `tests/unit/inc4/test_comisiones_query_controller.py` (5 tests)
- Integración: `tests/integration/inc4/test_comision_query_repository.py` (4),
  `tests/integration/inc4/test_comisiones_query_router.py` (6),
  `tests/integration/inc4/test_comision_consulta_port_in_process.py` (2)
- Suite completa: 384/384 unitarios, 259/259 integración — sin regresiones.
