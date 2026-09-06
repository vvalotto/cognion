# Plan de Implementación: US-4.2.1 - Docente consulta el desempeño de un estudiante elegido

**Patrón:** clean-architecture-bc (BC-first: entities → use_cases → interface_adapters → frameworks)
**Producto:** analytics

## Contexto de diseño

`ObtenerDesempenoEstudianteUseCase` (`US-4.1.2`) no cambia — el mismo cálculo sirve para el
Docente, solo cambia el origen de `estudiante_id` (path en vez de token) y el rol exigido.
Falta un puerto propio de Analytics para validar que `estudiante_id` existe (404) — Analytics
no puede importar el puerto `EstudianteConsultaPort` de `actividad_evaluativa` (serían dos BCs
comunicándose sin pasar por sus propios puertos, `CLAUDE.md` regla de imports). Se replica el
mismo patrón ya usado en `src/actividad_evaluativa` (adapter in-process hacia
`SQLAlchemyUsuarioRepository` de Identidad), con puerto propio de Analytics.

## Componentes a Implementar

### 1. Puerto de consulta de Estudiante (entities)
- [x] `src/analytics/entities/ports/estudiante_consulta_port.py`
  - `EstudianteConsultaPort` (ABC): método `existe(estudiante_id: UUID) -> bool`
  - Mismo contrato que `src/actividad_evaluativa/entities/ports/estudiante_consulta_port.py`,
    copia propia de Analytics — sin import cruzado entre BCs

### 2. Adapter in-process (frameworks)
- [x] `src/analytics/frameworks/adapters/estudiante_consulta_port_in_process.py`
  - `EstudianteConsultaPortInProcess`: implementa `existe()` invocando
    `SQLAlchemyUsuarioRepository.obtener_por_id()` de Identidad y verificando
    `TipoPerfil.ESTUDIANTE` — único punto de Analytics que importa `src.identidad`
    (mismo criterio que `estudiante_consulta_port_in_process.py` de Actividad Evaluativa)

### 3. Controller (interface_adapters)
- [x] `src/analytics/interface_adapters/controllers/analytics_controller.py`
  - Nuevo método `obtener_desempeno_de_estudiante(estudiante_id: UUID, materia_id: UUID) -> DesempenoEstudiante`
  - Delega en el mismo `ObtenerDesempenoEstudianteUseCase.execute()` ya inyectado — sin
    cambios en el Use Case ni en su firma

### 4. Router y DI (frameworks)
- [x] `src/analytics/frameworks/dependencies.py`
  - `require_docente = require_rol([TipoPerfil.DOCENTE], get_current_user)`
  - `get_estudiante_consulta_port(session: SessionDep) -> EstudianteConsultaPort`
- [x] `src/analytics/frameworks/api/analytics_router.py`
  - Nuevo endpoint `GET /materias/{materia_id}/estudiantes/{estudiante_id}/desempeno`
    (`dependencies=[Depends(require_docente)]`)
  - Valida `estudiante_consulta.existe(estudiante_id)` antes de invocar el controller;
    `HTTPException(404)` si no existe
  - Reutiliza `_a_response()` y `DesempenoEstudianteResponse` ya existentes (mismo shape que
    `US-4.1.2`, sin schema nuevo)

## Integración

- [ ] Sin cambios en `ObtenerDesempenoEstudianteUseCase` ni en `EvaluacionDesempenoConsultaPort`
      (`US-4.1.1`/`US-4.1.2`) — se reutilizan tal cual
- [ ] Sin cambios en `src/identidad/` — se consume `SQLAlchemyUsuarioRepository` ya existente

**Estado:** 4/4 tareas completadas
